from concurrent import futures
import logging
import grpc
import argparse
import quorum_registry_pb2, quorum_registry_pb2_grpc, quorum_replica_pb2, quorum_replica_pb2_grpc
import random


class Maintain(quorum_registry_pb2_grpc.MaintainServicer):
    def __init__(self, logger, N):
        self.logger = logger
        if N[0] >= N[1] + N[2]:
            raise ValueError("Invalid number of replicas (>= than read+write))")
        if N[2] <= N[0] / 2:
            raise ValueError("Invalid number of write replicas (write less than half)")
        self.N = N[0]
        self.Nr = N[1]
        self.Nw = N[2]
        self.registered = quorum_registry_pb2.Server_book()
        super().__init__()

    def RegisterServer(self, request, context):
        self.logger.info(
            "JOIN REQUEST FROM %s",
            context.peer(),
        )

        # check if server is already registered
        if any(
            i.ip == request.ip and i.port == request.port
            for i in self.registered.servers
        ):
            self.logger.warning("Server already registered")
            return quorum_registry_pb2.Success(value=False)

        self.registered.servers.add(ip=request.ip, port=request.port)
        return quorum_registry_pb2.Success(value=True)

    def GetAllReplicas(self, request, context):
        self.logger.info(
            "SERVER LIST REQUEST FROM %s",
            context.peer(),
        )
        return self.registered

    def GetWriteReplicas(self, request, context):
        # choose Nw random servers

        self.logger.info(
            "SERVER LIST REQUEST FROM %s",
            context.peer(),
        )
        return quorum_registry_pb2.Server_book(
            servers=random.sample(self.registered.servers, self.Nw)
        )

    def GetReadReplicas(self, request, context):
        # choose Nr random servers

        self.logger.info(
            "SERVER LIST REQUEST FROM %s",
            context.peer(),
        )
        return quorum_registry_pb2.Server_book(
            servers=random.sample(self.registered.servers, self.Nr)
        )


def serve(logger, EXPOSE_IP, PORT, N):
    port = str(PORT)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
    quorum_registry_pb2_grpc.add_MaintainServicer_to_server(Maintain(logger, N), server)
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
    agr.add_argument("--n", type=int, help="number of replicas", default=3)
    agr.add_argument("--nr", type=int, help="number of read replicas", default=3)
    agr.add_argument("--nw", type=int, help="number of replicas", default=3)

    args = agr.parse_args()

    EXPOSE_IP = args.ip
    PORT = args.port
    LOGFILE = args.log
    N = (args.n, args.nr, args.nw)

    logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    serve(logger, EXPOSE_IP, PORT, N)
