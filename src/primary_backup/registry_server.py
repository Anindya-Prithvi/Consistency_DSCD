from concurrent import futures
import logging
import grpc
import argparse
import registry_server_pb2, registry_server_pb2_grpc, replica_pb2, replica_pb2_grpc

class Maintain(registry_server_pb2_grpc.MaintainServicer):
    primary_replica = None
    registered = registry_server_pb2.Server_book()

    def __init__(self, logger):
        self.logger = logger
        super().__init__()

    def RegisterServer(self, request, context):
        self.logger.info(
            "JOIN REQUEST FROM %s",
            context.peer(),
        )

        # check if server is already registered
        if any(i.ip == request.ip and i.port == request.port for i in self.registered.servers):
            self.logger.warning("Server already registered")
            return registry_server_pb2.Server_information(
                ip=self.primary_replica.ip, port=self.primary_replica.port
            )

        self.registered.servers.add(ip=request.ip, port=request.port)

        
        if self.primary_replica is None:
            self.primary_replica = registry_server_pb2.Server_information(
                ip=request.ip, port=request.port
            )
        else:
            with grpc.insecure_channel(
                self.primary_replica.ip + ":" + self.primary_replica.port
            ) as channel:
                stub = replica_pb2_grpc.PrimeraStub(channel)
                response = stub.RecvReplica(request)
                self.logger.info(
                    f"Primary replica informed of new replica: {response.value}"
                )

        return registry_server_pb2.Server_information(
            ip=self.primary_replica.ip, port=self.primary_replica.port
        )

    def GetServerList(self, request, context):
        self.logger.info(
            "SERVER LIST REQUEST FROM %s",
            context.peer(),
        )
        return self.registered


def serve(logger, EXPOSE_IP, PORT):
    port = str(PORT)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
    registry_server_pb2_grpc.add_MaintainServicer_to_server(Maintain(logger), server)
    server.add_insecure_port(EXPOSE_IP + ":" + port)  # no TLS moment
    server.start()

    logger.info("Registry started, listening on all interfaces at port: " + port)
    logger.info("Press Ctrl+C to stop the server")
    server.wait_for_termination()


if __name__ == "__main__":
    logger = logging.getLogger("registrar")
    logger.setLevel(logging.INFO)
    EXPOSE_IP = "[::]"
    PORT = 1337  # default
    LOGFILE = None  # default
    

    # get sys args
    agr = argparse.ArgumentParser()
    agr.add_argument(
        "--ip",
        type=str,
        help="ip address to listen at, default [::] (all)",
        default=EXPOSE_IP,
    )
    agr.add_argument("--port", type=int, help="port number", default=PORT)
    agr.add_argument("--log", type=str, help="log file name", default=LOGFILE)

    args = agr.parse_args()

    EXPOSE_IP = args.ip
    PORT = args.port
    LOGFILE = args.log

    logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    serve(logger, EXPOSE_IP, PORT)
