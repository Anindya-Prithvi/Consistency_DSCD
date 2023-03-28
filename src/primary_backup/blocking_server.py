from concurrent import futures
from functools import reduce
import uuid
import logging
import grpc
import argparse
import registry_server_pb2, registry_server_pb2_grpc, replica_pb2, replica_pb2_grpc
import os
import time
import datetime

class Primera(replica_pb2_grpc.PrimeraServicer):
    def __init__(self, logger, REPLICAS):
        self.logger = logger
        self.REPLICAS = REPLICAS
        super().__init__()

    def RecvReplica(self, request, context):
        self.logger.info("RECEIVED NEW REGISTERED SERVER")
        # check if already in self.REPLICAS.servers
        if any(i.ip == request.ip and i.port == request.port for i in self.REPLICAS.servers):
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
        fobj = os.open("replicas/" + str(self.server_id) + "/" + request.name, os.O_CREAT | os.O_WRONLY)
        os.write(fobj, request.content.encode())
        os.close(fobj)
        # add to map
        self.UUID_MAP[request.uuid] = (request.name, request.version)
        return registry_server_pb2.Success(value=True)

    def DeleteBackup(self, request, context):
        self.logger.info("DELETE FROM PRIMERA")
        # delete file
        os.remove("replicas/" + str(self.server_id) + "/" + request.name)
        # deref in map, timestamp of deletion
        self.UUID_MAP[request.uuid] = ("", "WHATEVER primera gave")
        return registry_server_pb2.Success(value=True)

def SendToBackups(request, known_replica):
    with grpc.insecure_channel(
        known_replica.ip + ":" + known_replica.port
    ) as channel:
        stub = replica_pb2_grpc.BackupStub(channel)
        response = stub.WriteBackup(request)
        return response.value

class Serve(replica_pb2_grpc.ServeServicer):

    def __init__(self, logger, IS_PRIMARY, PRIMARY_SERVER, UUID_MAP, REPLICAS, _server_id):
        self.logger = logger
        self.IS_PRIMARY = IS_PRIMARY
        self.PRIMARY_SERVER = PRIMARY_SERVER
        self.UUID_MAP = UUID_MAP
        self.REPLICAS = REPLICAS
        self._server_id = _server_id
        super().__init__()    
    
    def Write(self, request, context):
        # TODO: Handle mentioned cases
        self.logger.info("WRITE REQUEST FROM %s", context.peer())
        # send to primary replica
        if self.IS_PRIMARY:
            # write to file
            fobj = os.open("replicas/" + str(self._server_id) + "/" + request.name, os.O_CREAT | os.O_WRONLY)
            os.write(fobj, request.content.encode())
            os.close(fobj)
            # add to map
            # Calculate version
            version = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            request.version = version
            self.UUID_MAP[request.uuid] = (request.name, request.version)
            # send to backups using thread worker pool

            ff_tpool = futures.ThreadPoolExecutor(max_workers=20)
            ff = ff_tpool.map(
                SendToBackups,
                [request] * len(self.REPLICAS.servers),
                self.REPLICAS.servers,
            )

            # accumulate return values
            # check if all backups succeeded

            if reduce(lambda x, y: x and y, ff):
                return replica_pb2.FileObject(
                    status = "Success",
                    uuid=request.uuid, 
                    version=version
                )
            else:
                return registry_server_pb2.Success(value=False)
        else:
            with grpc.insecure_channel(
                self.PRIMARY_SERVER.ip + ":" + self.PRIMARY_SERVER.port
            ) as channel:
                stub = replica_pb2_grpc.ServeStub(channel)
                response = stub.Write(request)
                return response

    def Read(self, request, context):
        # TODO: Handle the mentioned cases
        self.logger.info("READ REQUEST FROM %s", context.peer())
        # get name from UUID_MAP
        filename = self.UUID_MAP[request.uuid][0]

        # if file in fs
        try:
            with open("replicas/" + str(self._server_id) + "/" + filename, "r") as f:
                data = f.read()
            return replica_pb2.FileObject(
                status = "Success",
                name = filename,
                version=self.UUID_MAP[request.uuid][1], 
                content=data
            )
        except FileNotFoundError:
            return replica_pb2.FileObject(
                status = "File not found",
                uuid=request.uuid
            )

    def Delete(self, request, context):
        return super().Delete(request, context)


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
    replica_pb2_grpc.add_ServeServicer_to_server(Serve(logger,IS_PRIMARY, PRIMARY_SERVER, UUID_MAP, REPLICAS, _server_id), server)

    if IS_PRIMARY:
        replica_pb2_grpc.add_PrimeraServicer_to_server(Primera(logger,REPLICAS), server)
    else:
        replica_pb2_grpc.add_BackupServicer_to_server(Backup(logger,UUID_MAP, _server_id), server)
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
    
    #TODO: Handle edge cases in read/write/delete, only basics done
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
