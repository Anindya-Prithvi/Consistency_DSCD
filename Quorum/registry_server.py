# Registry server:
# [done] 1. The registry server resides at a known address (ip + port)
# [done] 2. The registry server stores each replica’s ip address (localhost) and port number -
#           localhost:8888
# [done] 3. Whenever a new replica comes up, it informs the registry server of its liveness
# [done]    a. Each replica shares its ip address and port with the registry server.
# [done]    b. Registry server marks the first replica as the primary replica.
# [done]    c. In response to each replica, the registry server always sends the information (ip +
#              port) about the primary server.
#           d. The registry server also needs to tell the primary replica about the joining of a
#               new replica (send the ip + port of the new replica to the primary replica).
# [done] 4. A client should get the list of replicas (list of ip address + port) from the registry server on
# startup.

# Majority of code adopted from our implementation of assignment 1 (obviosly)
from concurrent import futures
import logging
import grpc
import argparse
import registry_server_pb2
import registry_server_pb2_grpc
import random

logger = logging.getLogger("registrar")
logger.setLevel(logging.INFO)
MAXSERVERS = 500  # default, changeable by command line arg
EXPOSE_IP = "[::]"
PORT = 1337  # default
LOGFILE = None  # default
global N_r
global N_w
global N

registered = registry_server_pb2.Server_book()


class Maintain(registry_server_pb2_grpc.MaintainServicer):
    def RegisterServer(self, request, context):
        logger.info(
            "JOIN REQUEST FROM %s",
            context.peer(),
        )

        registered.servers.add(ip=request.ip, port=request.port)
        
        return registry_server_pb2.Server_information(
            ip=request.ip, port=request.port
        )

    def GetServerList(self, request, context):
        logger.info(
            "SERVER LIST REQUEST FROM %s",
            context.peer(),
        )
        return registered
    
    def GetReadReplicas(self, request, context):
        logger.info(
            "READ REPLICA LIST REQUEST FROM %s",
            context.peer(),
        )
        return registry_server_pb2.Server_book(servers=random.sample(registered.servers, N_r))

    def GetWriteReplicas(self, request, context):
        logger.info(
            "WRITE REPLICA LIST REQUEST FROM %s",
            context.peer(),
        )
        return registry_server_pb2.Server_book(servers=random.sample(registered.servers, N_w))

def serve():
    port = str(PORT)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    registry_server_pb2_grpc.add_MaintainServicer_to_server(Maintain(), server)
    server.add_insecure_port(EXPOSE_IP+":" + port)  # no TLS moment
    server.start()

    logger.info("Registry started, listening on all interfaces at port: " + port)
    logger.info("Press Ctrl+C to stop the server")

    while True:
        try:
            N_r = int(input("Enter the read quorum size (N_r): "))
            N_w = int(input("Enter the write quorum size (N_w): "))
            N = int(input("Enter the total number of replicas (N): "))
            if N_r + N_w <= N or N_w <= N / 2:
                raise ValueError
            else:
                logger.info("Registry server is ready to accept requests")
        except ValueError:
            logger.warning("Invalid quorum size, please try again")
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
    agr.add_argument("--ip", type=str, help="ip address (retrieve from ipconfig), default [::] (all)", default=EXPOSE_IP)
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
