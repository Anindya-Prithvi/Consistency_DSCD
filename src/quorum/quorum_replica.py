from concurrent import futures
from functools import reduce
import uuid
import logging
import grpc
import argparse
import quorum_registry_pb2, quorum_registry_pb2_grpc, quorum_replica_pb2, quorum_replica_pb2_grpc
import os
from time import sleep
import datetime

# TO SIMULATE REALTIME WRITE DELAYS IN BACKUPS (PER GC Comments), sleep is added


class Serve(quorum_replica_pb2_grpc.ServeServicer):
    def __init__(
        self, logger, UUID_MAP, _server_id
    ):
        self.logger = logger
        self.UUID_MAP = UUID_MAP
        self._server_id = _server_id
        super().__init__()

    def Write(self, request, context):
        self.logger.info("WRITE REQUEST FROM %s", context.peer())
        # check uuid exists
        uuid_exists = request.uuid in self.UUID_MAP
        # Scenario 4
        if uuid_exists and self.UUID_MAP[request.uuid][0] == "":
            return quorum_replica_pb2.FileObject(status="DELETED FILE CANNOT BE UPDATED")
        fixfilename = f"'{request.name}'"
        # fixfilename = fixfilename.replace("/", "_") # sanitizer
        # Scenario 2, check if file exists
        if not uuid_exists and os.path.exists(
            "replicas/" + str(self._server_id) + "/" + fixfilename
        ):
            return quorum_replica_pb2.FileObject(status="FILE WITH SAME NAME ALREADY EXISTS")

    
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
        
        self.UUID_MAP[request.uuid] = (fixfilename, version)
        # send to backups using thread worker pool

        request.name = fixfilename
        return quorum_replica_pb2.FileObject(
            status="SUCCESS", uuid=request.uuid, version=version
        )


    def Read(self, request, context):
        self.logger.info("READ REQUEST FROM %s", context.peer())

        # scenario 1, uuid not in map
        if request.uuid not in self.UUID_MAP:
            return quorum_replica_pb2.FileObject(status="FILE DOES NOT EXIST")

        # get name from UUID_MAP
        filename = self.UUID_MAP[request.uuid][0]

        # if file in fs
        try:
            with open("replicas/" + str(self._server_id) + "/" + filename, "r") as f:
                data = f.read()

            # scenario 2, everything goes well
            return quorum_replica_pb2.FileObject(
                status="SUCCESS",
                name=filename,
                version=self.UUID_MAP[request.uuid][1],
                content=data,
            )
        except (FileNotFoundError, PermissionError) as e:
            # scenario 3, file not in fs
            return quorum_replica_pb2.FileObject(
                status="FILE ALREADY DELETED", uuid=request.uuid
            )

    def Delete(self, request, context):
        # calculate deletion time if PRIMARY
        # check if uuid exists, scenario 1
        if request.uuid not in self.UUID_MAP:
            return quorum_replica_pb2.FileObject(status="FILE DOES NOT EXIST")
        # delete from primary
        filename = self.UUID_MAP[request.uuid][0]

        # check if file exists, in UUID_MAP, scenario 3
        if filename == "":
            return quorum_replica_pb2.FileObject(status="FILE ALREADY DELETED")

    
        # delete file, scenario 2
        os.remove("replicas/" + str(self._server_id) + "/" + filename)

        version = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.UUID_MAP[request.uuid] = ("", version)
        request.version = version

        return quorum_replica_pb2.FileObject(
            status="SUCCESS",
            # version=version # not needed
        )


def serve(logger, REGISTRY_ADDR, _server_id, EXPOSE_IP, PORT):
    # make directory for self.replicas files
    if not os.path.exists("replicas"):
        os.mkdir("replicas")

    # then make directory for itself
    if not os.path.exists("replicas/" + str(_server_id)):
        os.mkdir("replicas/" + str(_server_id))

    port = str(PORT)
    # connect to registry
    with grpc.insecure_channel(REGISTRY_ADDR) as channel:
        stub = quorum_registry_pb2_grpc.MaintainStub(channel)
        response = stub.RegisterServer(
            quorum_registry_pb2.Server_information(ip=EXPOSE_IP, port=port)
        )
        if response.value:
            logger.info("Successfully registered with registry")
        else:
            logger.critical("Failed to register with registry. No response")
            exit(1)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    UUID_MAP = {}
    quorum_replica_pb2_grpc.add_ServeServicer_to_server(
        Serve(logger, UUID_MAP, _server_id),
        server,
    )

    server.add_insecure_port(EXPOSE_IP + ":" + port)  # no TLS moment
    server.start()

    logger.info("Registry started, listening on all interfaces at port: " + port)
    logger.info("Press Ctrl+C to stop the server")

    server.wait_for_termination()


if __name__ == "__main__":
    _server_id = str(uuid.uuid4())[:6]  # private
    logger = logging.getLogger(f"server-{_server_id}")
    logger.setLevel(logging.INFO)
    LOGFILE = None  # default
    REGISTRY_ADDR = "[::1]:1337"
    EXPOSE_IP = "[::1]"
    PORT = None

    # TODO: Handle edge cases in read/write/delete, only basics done
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
