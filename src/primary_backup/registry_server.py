from concurrent import futures
import logging
import grpc
import argparse
import registry_server_pb2
import registry_server_pb2_grpc
import replica_pb2
import replica_pb2_grpc


logger = logging.getLogger("registrar")
logger.setLevel(logging.INFO)
MAXSERVERS = 500  # default, changeable by command line arg
EXPOSE_IP = "[::]"
PORT = 1337  # default
LOGFILE = None  # default

registered = registry_server_pb2.Server_book()
primary_replica = None


class Maintain(registry_server_pb2_grpc.MaintainServicer):
    def RegisterServer(self, request, context):
        logger.info(
            "JOIN REQUEST FROM %s",
            context.peer(),
        )

        # check if server is already registered
        if any(i.ip == request.ip and i.port == request.port for i in registered.servers):
            logger.warning("Server already registered")
            return registry_server_pb2.Server_information(
                ip=primary_replica.ip, port=primary_replica.port
            )

        registered.servers.add(ip=request.ip, port=request.port)

        global primary_replica
        if primary_replica is None:
            primary_replica = registry_server_pb2.Server_information(
                ip=request.ip, port=request.port
            )
        else:
            with grpc.insecure_channel(
                primary_replica.ip + ":" + primary_replica.port
            ) as channel:
                stub = replica_pb2_grpc.PrimeraStub(channel)
                response = stub.RecvReplica(request)
                logger.info(
                    f"Primary replica informed of new replica: {response.value}"
                )

        return registry_server_pb2.Server_information(
            ip=primary_replica.ip, port=primary_replica.port
        )

    def GetServerList(self, request, context):
        logger.info(
            "SERVER LIST REQUEST FROM %s",
            context.peer(),
        )
        return registered


def serve():
    port = str(PORT)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    registry_server_pb2_grpc.add_MaintainServicer_to_server(Maintain(), server)
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
        "--ip",
        type=str,
        help="ip address to listen at, default [::] (all)",
        default=EXPOSE_IP,
    )
    agr.add_argument("--port", type=int, help="port number", default=PORT)
    agr.add_argument(
        "--max", type=int, help="maximum number of servers", default=MAXSERVERS
    )
    agr.add_argument("--log", type=str, help="log file name", default=LOGFILE)

    args = agr.parse_args()

    EXPOSE_IP = args.ip
    PORT = args.port
    MAXSERVERS = args.max
    LOGFILE = args.log

    logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    serve()
