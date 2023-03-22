# Registry server:
# 1. The registry server resides at a known address (ip + port)
# 2. The registry server stores each replica’s ip address (localhost) and port number -
# localhost:8888
# 3. Whenever a new replica comes up, it informs the registry server of its liveness
    # a. Each replica shares its ip address and port with the registry server.
    # b. Registry server marks the first replica as the primary replica.
    # c. In response to each replica, the registry server always sends the information (ip +
    # port) about the primary server.
    # d. The registry server also needs to tell the primary replica about the joining of a
    # new replica (send the ip + port of the new replica to the primary replica).
# 4. A client should get the list of replicas (list of ip address + port) from the registry server on
# startup.

# Majority of code adopted from our implementation of assignment 1 (obviosly)
from concurrent import futures
import logging

import sys
import grpc
import registry_server_pb2
import registry_server_pb2_grpc

logger = logging.getLogger("registrar")
logger.setLevel(logging.INFO)
MAXSERVERS = 5  # default, changeable by command line arg

registered = registry_server_pb2.Server_book()


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
        new_server = registered.servers.add()
        new_server.name = request.name
        new_server.addr = request.addr
        return registry_server_pb2.Success(value=True)

    def GetServerList(self, request, context):
        logger.info(
            "SERVER LIST REQUEST FROM %s with id %s",
            context.peer(),
            request.id,
        )
        return registered


def serve():
    port = "1337"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    registry_server_pb2_grpc.add_MaintainServicer_to_server(Maintain(), server)
    server.add_insecure_port("[::]:" + port) #no TLS moment
    server.start()
    print("Registry started, listening on all interfaces at port: " + port)
    server.wait_for_termination() # no need for thread anymore


if __name__ == "__main__":
    # get sys args

    if len(sys.argv) > 1:
        try:
            MAXSERVERS = int(sys.argv[1])
        except ValueError:
            print("Invalid number of servers")
            print("Usage: python registry_server.py [number of servers]")
            sys.exit(1)
    logging.basicConfig()
    serve()