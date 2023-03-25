# Any client can interact with any replica directly. There can be multiple clients
# concurrently interacting with the data store.

# Each file can be assumed to be very small in size ( 200-500 characters)


from concurrent import futures
import uuid
import logging
import grpc
import argparse
import replica_pb2
import replica_pb2_grpc
import registry_server_pb2
import registry_server_pb2_grpc
import os

_server_id = str(uuid.uuid4())[:6]  # private
logger = logging.getLogger(f"server-{_server_id}")
logger.setLevel(logging.INFO)
LOGFILE = None  # default
REGISTRY_ADDR = "localhost:1337"
EXPOSE_IP = "[::]"
PORT = None
PRIMARY_SERVER = None # no one is primary
IS_PRIMARY = False
REPLICAS = registry_server_pb2.Server_book()

# make directory for replicas files
if not os.path.exists("replicas"):
    os.mkdir("replicas")

# then make directory for itself
if not os.path.exists("replicas/" + str(_server_id)):
    os.mkdir("replicas/" + str(_server_id))

class Serve(replica_pb2_grpc.ServeServicer):
    # TODO: All 3
    def Write(self, request, context):
        logger.info("WRITE REQUEST FROM %s", context.peer())
        # send to primary replica
        if IS_PRIMARY:
            # write to file
            with open(request.filename, "w") as f:
                f.write(request.data)
            return registry_server_pb2.Success(value=True)
        else:
            with grpc.insecure_channel(PRIMARY_SERVER.ip + ":" + PRIMARY_SERVER.port) as channel:
                stub = replica_pb2_grpc.ServeStub(channel)
                response = stub.Write(request)
                return response

    def Read(self, request, context):
        logger.info("READ REQUEST FROM %s", context.peer())
        # if file in fs
        try:
            with open(request.filename, "r") as f:
                data = f.read()
            return replica_pb2.File(data=data)
        except FileNotFoundError:
            return replica_pb2.File(data="")
        
    def Delete(self, request, context):
        return super().Delete(request, context)
    # below for reference
    # def RegisterServer(self, request, context):
    #     logger.info(
    #         "JOIN REQUEST FROM %s",
    #         context.peer(),
    #     )
    #     if len(registered.servers) >= MAXSERVERS:
    #         return registry_server_pb2.Success(value=False)
    #     if any(
    #         i.id == request.id or i.addr == request.addr for i in registered.servers
    #     ):
    #         return registry_server_pb2.Success(value=False)

    #     registered.servers.add(id=request.id, addr=request.addr)
    #     if primary_replica is None:
    #         primary_replica = (request.ip, request.port)
    #     else:
    #         pass

    #     return registry_server_pb2.Server_information(
    #         ip=primary_replica[0], port=primary_replica[1]
    #     )

    # def GetServerList(self, request, context):
    #     logger.info(
    #         "SERVER LIST REQUEST FROM %s",
    #         context.peer(),
    #     )
    #     return registered


def serve():
    # TODO: server cleints
    port = str(PORT)

    # connect to registry
    with grpc.insecure_channel(REGISTRY_ADDR) as channel:
        stub = registry_server_pb2_grpc.MaintainStub(channel)
        response = stub.RegisterServer(
            registry_server_pb2.Server_information(
                ip=EXPOSE_IP, port=port
            )
        )
        if response.value:
            logger.info("Successfully registered with registry")
            PRIMARY_SERVER = registry_server_pb2.Server_information(ip = response.ip, port = response.port)

            if response.ip == EXPOSE_IP and response.port == port:
                IS_PRIMARY = True
                logger.info("This is the primary replica")
        else:
            logger.critical("Failed to register with registry")
            exit(1)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    replica_pb2_grpc.add_ServeServicer_to_server(Serve(), server)
    server.add_insecure_port(EXPOSE_IP+":" + port)  # no TLS moment
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
    agr.add_argument("--ip", type=str, help="ip address of server (default 0.0.0.0)", default="0.0.0.0")
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
