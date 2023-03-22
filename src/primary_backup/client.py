# CLIENT 
# 1. WRITE operation
#    a. The client first generates a UUID for the new file.
#       i. If it is updating an existing file, then it reuses the same UUID which was
#          generated previously.
#    b. Client then sends uuid, filename, and content of the text file to any one replica.
#    c. Replica responds back with the uuid of the saved text file and version timestamp.

"""
For example:
Client sends -
Name : "Formula1ChampionsList"
Content : "M. Schumacher, L. Hamilton, J.M. Fangio."
UUID : 03ff7ebe-bf8e-11ed-89d9-76aef1e817c5
Server sends -
Status: SUCCESS
UUID : 03ff7ebe-bf8e-11ed-89d9-76aef1e817c5
Version : "12/03/2023 11:15:11
"""

import uuid
import logging
import grpc
import argparse
import registry_server_pb2
import registry_server_pb2_grpc

_client_id = uuid.uuid4() #private
logger = logging.getLogger(f"client-{str(_client_id)[:6]}")
logger.setLevel(logging.INFO)
LOGFILE = None  # default
REGISTRY_ADDR = "localhost:1337"

def get_served():
    #TODO: add receiving logic
    # fetch replicas from registry server
    with grpc.insecure_channel(REGISTRY_ADDR) as channel:
        stub = registry_server_pb2_grpc.MaintainStub(channel)
        response = stub.GetServerList(registry_server_pb2.Empty())
        logger.info(f"Got server list from registry server {response.servers}")



if __name__ == "__main__":
    # get sys args
    
    agr = argparse.ArgumentParser()
    agr.add_argument("--log", type=str, help="log file name", default=None)
    agr.add_argument("--addr", type=str, help="address of registry server if customized", default=REGISTRY_ADDR)

    args = agr.parse_args()
    LOGFILE = args.log
    REGISTRY = args.addr

    logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    get_served()