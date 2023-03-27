# Any client can interact with any replica directly. There can be multiple clients
# concurrently interacting with the data store.

# Each file can be assumed to be very small in size ( 200-500 characters)


from concurrent import futures
from functools import reduce
import uuid
import logging
import grpc
import argparse
import replica_pb2
import replica_pb2_grpc
import registry_server_pb2
import registry_server_pb2_grpc
import os
import time
import datetime

#TODO: Handle edge cases in read/write/delete, only basics done

_server_id = str(uuid.uuid4())[:6]  # private
logger = logging.getLogger(f"server-{_server_id}")
logger.setLevel(logging.INFO)
LOGFILE = None  # default
REGISTRY_ADDR = "[::1]:1337"
EXPOSE_IP = "[::1]"
PORT = None
PRIMARY_SERVER = None  # no one is primary
IS_PRIMARY = False
REPLICAS = registry_server_pb2.Server_book()
UUID_MAP = dict() # key, value = uuid, (name, version)

# make directory for replicas files
if not os.path.exists("replicas"):
    os.mkdir("replicas")

# then make directory for itself
if not os.path.exists("replicas/" + str(_server_id)):
    os.mkdir("replicas/" + str(_server_id))


class Primera(replica_pb2_grpc.PrimeraServicer):
    def RecvReplica(self, request, context):
        logger.info("RECEIVED NEW REGISTERED SERVER")
        # check if already in REPLICAS.servers
        if any(i.ip == request.ip and i.port == request.port for i in REPLICAS.servers):
            return registry_server_pb2.Success(value=False)
        else:
            REPLICAS.servers.add(ip=request.ip, port=request.port)
            return registry_server_pb2.Success(value=True)

class Backup(replica_pb2_grpc.BackupServicer):
    def WriteBackup(self, request, context):
        logger.info("WRITE FROM PRIMERA")
        # write to file
        fobj = os.open("replicas/" + str(_server_id) + "/" + request.name, os.O_CREAT | os.O_WRONLY)
        os.write(fobj, request.content.encode())
        os.close(fobj)
        # add to map
        UUID_MAP[request.uuid] = (request.name, request.version)
        return registry_server_pb2.Success(value=True)

    def DeleteBackup(self, request, context):
        logger.info("DELETE FROM PRIMERA")
        # delete file
        os.remove("replicas/" + str(_server_id) + "/" + request.name)
        # deref in map, timestamp of deletion formatted like "12/03/2023 11:15:11"
        UUID_MAP[request.uuid] = ("", datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        return registry_server_pb2.Success(value=True)


class Serve(replica_pb2_grpc.ServeServicer):
    # TODO: All 3
    def Write(self, request, context):
        logger.info("WRITE REQUEST FROM %s", context.peer())
        # send to primary replica
        if IS_PRIMARY:
            # write to file
            fobj = os.open("replicas/" + str(_server_id) + "/" + request.name, os.O_CREAT | os.O_WRONLY)
            os.write(fobj, request.content.encode())
            os.close(fobj)
            # add to map
            UUID_MAP[request.uuid] = (request.name, request.version)
            # send to backups using thread worker pool

            def SendToBackups(request, known_replica):
                with grpc.insecure_channel(
                    known_replica.ip + ":" + known_replica.port
                ) as channel:
                    stub = replica_pb2_grpc.BackupStub(channel)
                    response = stub.WriteBackup(request)
                    return response.value

            ff_tpool = futures.ThreadPoolExecutor(max_workers=20)
            ff = ff_tpool.map(
                SendToBackups,
                [request] * len(REPLICAS.servers),
                REPLICAS.servers,
            )

            # accumulate return values
            # check if all backups succeeded

            if reduce(lambda x, y: x and y, ff):
                return replica_pb2.FileObject(
                    status = "Success",
                    uuid=request.uuid, 
                    version=request.version
                )
            else:
                return registry_server_pb2.Success(value=False)
        else:
            with grpc.insecure_channel(
                PRIMARY_SERVER.ip + ":" + PRIMARY_SERVER.port
            ) as channel:
                stub = replica_pb2_grpc.ServeStub(channel)
                response = stub.Write(request)
                return response

    def Read(self, request, context):
        logger.info("READ REQUEST FROM %s", context.peer())
        # if file in fs
        try:
            with open(request.name, "r") as f:
                data = f.read()
            return replica_pb2.File(data=data)
        except FileNotFoundError:
            return replica_pb2.File(data="")

    def Delete(self, request, context):
        return super().Delete(request, context)


def serve():
    # TODO: server cleints
    port = str(PORT)

    # connect to registry
    with grpc.insecure_channel(REGISTRY_ADDR) as channel:
        stub = registry_server_pb2_grpc.MaintainStub(channel)
        response = stub.RegisterServer(
            registry_server_pb2.Server_information(ip=EXPOSE_IP, port=port)
        )
        if response:
            logger.info("Successfully registered with registry")
            global PRIMARY_SERVER
            PRIMARY_SERVER = registry_server_pb2.Server_information(
                ip=response.ip, port=response.port
            )

            if response.ip == EXPOSE_IP and response.port == port:
                global IS_PRIMARY
                IS_PRIMARY = True
                logger.info("This is the primary replica")
                # Launch primary replica receive service
        else:
            logger.critical("Failed to register with registry. No response")
            exit(1)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    replica_pb2_grpc.add_ServeServicer_to_server(Serve(), server)

    if IS_PRIMARY:
        replica_pb2_grpc.add_PrimeraServicer_to_server(Primera(), server)
    else:
        replica_pb2_grpc.add_BackupServicer_to_server(Backup(), server)
    server.add_insecure_port(EXPOSE_IP + ":" + port)  # no TLS moment
    server.start()

    logger.info("Registry started, listening on all interfaces at port: " + port)
    logger.info("Press Ctrl+C to stop the server")

    while True:
        try:
            _ = input()
        except KeyboardInterrupt:
            logger.info("Stopping server")
            server.stop(0)
            exit(0)
        except EOFError:
            logger.warning("Server will now go headless (no input from stdin)")
            server.wait_for_termination()
            exit(0)
        except:
            logger.critical("Critical error, stopping server")
            server.stop(None)
            exit(1)


if __name__ == "__main__":
    # get sys args

    agr = argparse.ArgumentParser()
    agr.add_argument(
        "--ip", type=str, help="ip address of server (default ::1)", default="[::1]"
    )
    agr.add_argument("--port", type=int, help="port number", required=True)
    agr.add_argument("--log", type=str, help="log file name", default=None)
    agr.add_argument(
        "--addr",
        type=str,
        help="address of registry server if customized",
        default=REGISTRY_ADDR,
    )

    args = agr.parse_args()
    LOGFILE = args.log
    REGISTRY = args.addr
    PORT = args.port
    EXPOSE_IP = args.ip

    logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    serve()
