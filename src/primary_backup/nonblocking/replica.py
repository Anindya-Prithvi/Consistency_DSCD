from concurrent import futures
from functools import reduce
import queue
import uuid
import logging
import grpc
import argparse
import registry_server_pb2, registry_server_pb2_grpc, replica_pb2, replica_pb2_grpc
import os
from time import sleep
import datetime
from copy import deepcopy

# TO SIMULATE REALTIME WRITE DELAYS IN BACKUPS (PER GC Comments), sleep is added


class Primera(replica_pb2_grpc.PrimeraServicer):
    def __init__(self, logger, REPLICAS):
        self.logger = logger
        self.REPLICAS = REPLICAS
        super().__init__()

    def RecvReplica(self, request, context):
        self.logger.info("RECEIVED NEW REGISTERED SERVER")
        # check if already in self.REPLICAS.servers
        if any(
            i.ip == request.ip and i.port == request.port for i in self.REPLICAS.servers
        ):
            return registry_server_pb2.Success(value=False)
        else:
            self.REPLICAS.servers.add(ip=request.ip, port=request.port)
            return registry_server_pb2.Success(value=True)


class Backup(replica_pb2_grpc.BackupServicer):
    def __init__(self, logger, UUID_MAP, server_id):
        self.logger = logger
        self.UUID_MAP = UUID_MAP
        self.server_id = server_id
        super().__init__()

    def WriteBackup(self, request, context):
        self.logger.info("WRITE FROM PRIMERA")
        # write to file
        fobj = os.open(
            "replicas/" + str(self.server_id) + "/" + request.name,
            os.O_CREAT | os.O_WRONLY,
        )
        os.write(fobj, request.content.encode())
        os.close(fobj)

        # COMMENT BELOW FOR NO DELAY
        import random

        sleep(random.randint(0, 3_000_000) / 1_000_000)

        # add to map
        self.UUID_MAP[request.uuid] = (request.name, request.version)
        return registry_server_pb2.Success(value=True)

    def DeleteBackup(self, request, context):
        self.logger.info("DELETE FROM PRIMERA")
        # delete file
        # get name from UUID_MAP
        name = self.UUID_MAP[request.uuid][0]

        os.remove("replicas/" + str(self.server_id) + "/" + name)
        # deref in map, timestamp of deletion
        self.UUID_MAP[request.uuid] = ("", request.version)
        return registry_server_pb2.Success(value=True)


def SendToBackups(request, known_replica, request_type: str):
    with grpc.insecure_channel(known_replica.ip + ":" + known_replica.port) as channel:
        stub = replica_pb2_grpc.BackupStub(channel)
        if request_type == "write":
            response = stub.WriteBackup(request)
        elif request_type == "delete":
            response = stub.DeleteBackup(request)
        return response.value


class Serve(replica_pb2_grpc.ServeServicer):
    def __init__(
        self, logger, IS_PRIMARY, PRIMARY_SERVER, UUID_MAP, REPLICAS, _server_id
    ):
        self.logger = logger
        self.IS_PRIMARY = IS_PRIMARY
        self.PRIMARY_SERVER = PRIMARY_SERVER
        self.UUID_MAP = UUID_MAP
        self.REPLICAS = REPLICAS
        self._server_id = _server_id
        self.pending_requests = queue.Queue()
        super().__init__()

    def Write(self, request, context):
        self.logger.info("WRITE REQUEST FROM %s", context.peer())
        # check uuid exists
        uuid_exists = request.uuid in self.UUID_MAP
        # Scenario 4
        if uuid_exists and self.UUID_MAP[request.uuid][0] == "":
            return replica_pb2.FileObject(status="DELETED FILE CANNOT BE UPDATED")
        fixfilename = f"'{request.name}'"
        # fixfilename = fixfilename.replace("/", "_") # sanitizer
        # Scenario 2, check if file exists
        if not uuid_exists and os.path.exists(
            "replicas/" + str(self._server_id) + "/" + fixfilename
        ):
            return replica_pb2.FileObject(status="FILE WITH SAME NAME ALREADY EXISTS")

        # send to primary replica
        if self.IS_PRIMARY:
            # write to file
            fobj = os.open(
                "replicas/" + str(self._server_id) + "/" + fixfilename,
                os.O_CREAT | os.O_WRONLY,
            )
            os.write(fobj, request.content.encode())
            os.close(fobj)
            # best case, scenario and also update (1,3)
            # add to map
            # Calculate version
            version = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            request.version = version
            self.UUID_MAP[request.uuid] = (fixfilename, request.version)
            # send to backups using thread worker pool

            request.name = fixfilename

            # just add to queue
            self.pending_requests.put((deepcopy(request), "write"))

            return replica_pb2.FileObject(
                status="SUCCESS", uuid=request.uuid, version=version
            )

        else:
            with grpc.insecure_channel(
                self.PRIMARY_SERVER.ip + ":" + self.PRIMARY_SERVER.port
            ) as channel:
                stub = replica_pb2_grpc.ServeStub(channel)
                resprim = stub.Write(request)
                return resprim

    def Read(self, request, context):
        self.logger.info("READ REQUEST FROM %s", context.peer())

        # scenario 1, uuid not in map
        if request.uuid not in self.UUID_MAP:
            return replica_pb2.FileObject(status="FILE DOES NOT EXIST")

        # get name from UUID_MAP
        filename = self.UUID_MAP[request.uuid][0]

        # if file in fs
        try:
            with open("replicas/" + str(self._server_id) + "/" + filename, "r") as f:
                data = f.read()

            # scenario 2, everything goes well
            return replica_pb2.FileObject(
                status="SUCCESS",
                name=filename,
                version=self.UUID_MAP[request.uuid][1],
                content=data,
            )
        except (FileNotFoundError, PermissionError) as e:
            # scenario 3, file not in fs
            return replica_pb2.FileObject(
                status="FILE ALREADY DELETED", uuid=request.uuid
            )

    def Delete(self, request, context):
        # calculate deletion time if PRIMARY
        # check if uuid exists, scenario 1
        if request.uuid not in self.UUID_MAP:
            return replica_pb2.FileObject(status="FILE DOES NOT EXIST")
        # delete from primary
        filename = self.UUID_MAP[request.uuid][0]

        # check if file exists, in UUID_MAP, scenario 3
        if filename == "":
            return replica_pb2.FileObject(status="FILE ALREADY DELETED")

        if self.IS_PRIMARY:
            # delete file, scenario 2
            os.remove("replicas/" + str(self._server_id) + "/" + filename)

            version = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.UUID_MAP[request.uuid] = ("", version)
            request.version = version

            # just add to queue
            self.pending_requests.put((deepcopy(request), "delete"))

            return replica_pb2.FileObject(
                status="SUCCESS",
                # version=version # not needed
            )

        else:
            with grpc.insecure_channel(
                self.PRIMARY_SERVER.ip + ":" + self.PRIMARY_SERVER.port
            ) as channel:
                stub = replica_pb2_grpc.ServeStub(channel)
                resprim = stub.Delete(request)
                return resprim


def serve(logger, REGISTRY_ADDR, _server_id, EXPOSE_IP, PORT):
    # make directory for self.replicas files
    if not os.path.exists("replicas"):
        os.mkdir("replicas")

    # then make directory for itself
    if not os.path.exists("replicas/" + str(_server_id)):
        os.mkdir("replicas/" + str(_server_id))

    port = str(PORT)
    IS_PRIMARY = False

    # connect to registry
    with grpc.insecure_channel(REGISTRY_ADDR) as channel:
        stub = registry_server_pb2_grpc.MaintainStub(channel)
        response = stub.RegisterServer(
            registry_server_pb2.Server_information(ip=EXPOSE_IP, port=port)
        )
        if response:
            logger.info("Successfully registered with registry")

            PRIMARY_SERVER = registry_server_pb2.Server_information(
                ip=response.ip, port=response.port
            )

            if response.ip == EXPOSE_IP and response.port == port:
                IS_PRIMARY = True
                logger.info("This is the primary replica")
                # Launch primary replica receive service
        else:
            logger.critical("Failed to register with registry. No response")
            exit(1)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    UUID_MAP = {}
    REPLICAS = registry_server_pb2.Server_book()
    main_serve = Serve(
        logger, IS_PRIMARY, PRIMARY_SERVER, UUID_MAP, REPLICAS, _server_id
    )
    replica_pb2_grpc.add_ServeServicer_to_server(
        main_serve,
        server,
    )

    if IS_PRIMARY:
        replica_pb2_grpc.add_PrimeraServicer_to_server(
            Primera(logger, REPLICAS), server
        )
    else:
        replica_pb2_grpc.add_BackupServicer_to_server(
            Backup(logger, UUID_MAP, _server_id), server
        )
    server.add_insecure_port(EXPOSE_IP + ":" + port)  # no TLS moment
    server.start()

    logger.info("Registry started, listening on all interfaces at port: " + port)
    logger.info("Press Ctrl+C to stop the server")

    non_block_write_through = futures.ThreadPoolExecutor(max_workers=20)

    while True:
        # check if there are pending requests
        request, operation = main_serve.pending_requests.get(block=True)
        if operation == "write":
            # send to all replicas
            ff = non_block_write_through.map(
                SendToBackups,
                [request] * len(main_serve.REPLICAS.servers),
                main_serve.REPLICAS.servers,
                ["write"] * len(main_serve.REPLICAS.servers),
            )
            if reduce(lambda x, y: x and y, ff):
                print("[PRIMERA], ALL BACKUPS RECEIVED")
        elif operation == "delete":
            # send to all replicas
            ff = non_block_write_through.map(
                SendToBackups,
                [request] * len(main_serve.REPLICAS.servers),
                main_serve.REPLICAS.servers,
                ["delete"] * len(main_serve.REPLICAS.servers),
            )
            if reduce(lambda x, y: x and y, ff):
                print("[PRIMERA], ALL BACKUPS RECEIVED")

    server.wait_for_termination()


if __name__ == "__main__":
    _server_id = str(uuid.uuid4())[:6]  # private
    logger = logging.getLogger(f"server-{_server_id}")
    logger.setLevel(logging.INFO)
    LOGFILE = None  # default
    REGISTRY_ADDR = "[::1]:1337"
    EXPOSE_IP = "[::1]"
    PORT = None

    # get sys args

    agr = argparse.ArgumentParser()
    agr.add_argument(
        "--ip", type=str, help="ip address of server (default ::1)", default="[::1]"
    )
    agr.add_argument("--port", type=int, help="port number", required=True)
    agr.add_argument("--log", type=str, help="log file name", default=None)
    agr.add_argument(
        "--raddr",
        type=str,
        help="address of registry server if customized",
        default=REGISTRY_ADDR,
    )

    args = agr.parse_args()
    LOGFILE = args.log
    REGISTRY = args.raddr
    PORT = args.port
    EXPOSE_IP = args.ip

    logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    serve(logger, REGISTRY_ADDR, _server_id, EXPOSE_IP, PORT)
