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
# 4. A client should get the list of replicas (list of ip address + port) from the registry server on
# startup.

# Majority of code adopted from our implementation of assignment 1 (obviosly)
from concurrent import futures
import logging
import grpc
import argparse
import registry_server_pb2
import registry_server_pb2_grpc

logger = logging.getLogger("registrar")
logger.setLevel(logging.INFO)
MAXSERVERS = 5  # default, changeable by command line arg
PORT = 1337     # default
LOGFILE = None  # default

registered = registry_server_pb2.Server_book()
primary_replica = None


class Maintain(registry_server_pb2_grpc.MaintainServicer):
    def RegisterServer(self, request, context):
        logger.info(
            "JOIN REQUEST FROM %s",
            context.peer(),
        )
        if len(registered.servers) >= MAXSERVERS:
            return registry_server_pb2.Success(value=False)
        if any(
            i.name == request.name or i.addr == request.addr for i in registered.servers
        ):
            return registry_server_pb2.Success(value=False)
        
        registered.servers.add(name = request.name, addr = request.addr)
        if primary_replica is None:
            primary_replica = (request.ip, request.port)
        else:
            #TODO: inform primary replica
            pass

        return registry_server_pb2.Server_information(ip = primary_replica[0], port = primary_replica[1])

    def GetServerList(self, request, context):
        logger.info(
            "SERVER LIST REQUEST FROM %s with id %s",
            context.peer(),
            request.id,
        )
        return registered


def serve():
    port = str(PORT)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    registry_server_pb2_grpc.add_MaintainServicer_to_server(Maintain(), server)
    server.add_insecure_port("[::]:" + port) #no TLS moment
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
    agr.add_argument("--port",type=int, help="port number", default=PORT)
    agr.add_argument("--max", type=int, help="maximum number of servers", default=MAXSERVERS)
    agr.add_argument("--log", type=str, help="log file name", default=LOGFILE)

    args = agr.parse_args()

    PORT = args.port
    MAXSERVERS = args.max
    LOGFILE = args.log

    logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    serve()