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

from concurrent import futures
import logging
import grpc
import argparse
import registry_server_pb2
import registry_server_pb2_grpc

logger = logging.getLogger("client")
logger.setLevel(logging.INFO)
LOGFILE = None  # default

def get_served():
    #TODO: add serving logic
    pass


if __name__ == "__main__":
    # get sys args
    
    agr = argparse.ArgumentParser()
    agr.add_argument("--log", type=str, help="log file name")

    args = agr.parse_args()
    LOGFILE = args.log

    logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    get_served()