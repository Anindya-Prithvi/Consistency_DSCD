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
import concurrent.futures
import argparse
import registry_server_pb2
import registry_server_pb2_grpc
import replica_pb2
import replica_pb2_grpc

_client_id = uuid.uuid4()  # private
logger = logging.getLogger(f"client-{str(_client_id)[:6]}")
logger.setLevel(logging.INFO)
LOGFILE = None  # default
REGISTRY_ADDR = "localhost:1337"
OPTIONS = """\
Please choose from the following options:
    1. WRITE
    2. READ
    3. DELETE
    4. EXIT\
"""

def write_server_helper(server, client_info):
    with grpc.insecure_channel(server.ip + ":" + server.port) as channel:
        stub = replica_pb2_grpc.Serve(channel)
        response = stub.Write(client_info)
        return response


def read_server_helper(server, client_info):
    with grpc.insecure_channel(server.ip + ":" + server.port) as channel:
        stub = replica_pb2_grpc.Serve(channel)
        response = stub.Read(client_info)
        return response


def delete_server_helper(server, client_info):
    with grpc.insecure_channel(server.ip + ":" + server.port) as channel:
        stub = replica_pb2_grpc.Serve(channel)
        response = stub.Delete(client_info)
        return response
    

def write_file(logger):
    #getting list of write quorum servers
    known_servers = []
    with grpc.insecure_channel(REGISTRY_ADDR) as channel:
        stub = registry_server_pb2_grpc.MaintainStub(channel)
        response = stub.GetWriteReplicas(registry_server_pb2.Empty())
        logger.info(f"List of write replicas {response.servers}")
        known_servers = response.servers

    #getting user input
    client_info = replica_pb2.ClientRequest()
    file_uuid = input("Enter the UUID of the file (leave blank if creating new file): ")
    if file_uuid == "":
        file_uuid = str(uuid.uuid4())
    client_info.uuid = file_uuid
    
    #getting file name and content
    while (True):
        try:
            file_name = input("Enter the name of the file: ")
            file_content = input("Enter the content of the file: ")
            if (file_name == "" or file_content == ""):
                raise ValueError
            else:
                client_info.name = file_name
                client_info.content = file_content
                break
        except ValueError:
            logger.error("Invalid input")
            continue
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt")
            return
        
    #sending request to write quorum servers
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = [executor.submit(write_server_helper, server, client_info) for server in known_servers]

    #getting response from write quorum servers
    for future in concurrent.futures.as_completed(results):
        response = future.result()
        if response.status == replica_pb2.Status.SUCCESS:
            logger.info(f"File written successfully with UUID {response.uuid} and version {response.timestamp}")
        else:
            logger.error(f"File not written successfully with UUID {response.uuid} and version {response.timestamp}")



def read_file(logger):
    known_servers = []
    with grpc.insecure_channel(REGISTRY_ADDR) as channel:
        stub = registry_server_pb2_grpc.MaintainStub(channel)
        response = stub.GetReadReplicas(registry_server_pb2.Empty())
        logger.info(f"List of read replicas {response.servers}")
        known_servers = response.servers

    #getting user input
    #TODO: check if file uuid exists or not
    while (True):
        try:
            client_info = replica_pb2.ClientRequest()
            file_uuid = input("Enter the UUID of the file (leave blank if creating new file): ")
            if (file_uuid == ""):
                raise ValueError
            else:
                client_info.uuid = file_uuid
                break
        except ValueError:
            logger.error("Invalid input")
            continue
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt")
            return

    #sending request to read quorum servers
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = [executor.submit(read_server_helper, server, client_info) for server in known_servers]

    #getting response from read quorum servers
    name_timestamp_mapping = {}
    for future in concurrent.futures.as_completed(results):
        response = future.result()
        if response.status == replica_pb2.Status.SUCCESS:
            name_timestamp_mapping[response.timestamp] = [response.name, response.content, response.uuid, response.status]
        
    #getting latest version of file
    max_key = max(name_timestamp_mapping, key=name_timestamp_mapping.get)
    logger.info(f"Status: {name_timestamp_mapping[max_key][3]}")
    logger.info(f"File name: {name_timestamp_mapping[max_key][0]}")
    logger.info(f"File content: {name_timestamp_mapping[max_key][1]}")
    logger.info(f"Version: {max_key}")


def delete_file(logger):
    known_servers = []
    with grpc.insecure_channel(REGISTRY_ADDR) as channel:
        stub = registry_server_pb2_grpc.MaintainStub(channel)
        response = stub.GetWriteReplicas(registry_server_pb2.Empty())
        logger.info(f"List of write replicas {response.servers}")
        known_servers = response.servers

    #getting user input
    #TODO: check if file uuid exists or not
    while (True):
        try:
            client_info = replica_pb2.ClientRequest()
            file_uuid = input("Enter the UUID of the file (leave blank if creating new file): ")
            if (file_uuid == ""):
                raise ValueError
            else:
                client_info.uuid = file_uuid
                break
        except ValueError:
            logger.error("Invalid input")
            continue
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt")
            return
    
    #sending request to write quorum servers
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = [executor.submit(write_server_helper, server, client_info) for server in known_servers]
    
    #getting response from write quorum servers
    for future in concurrent.futures.as_completed(results):
        response = future.result()
        if response.status == replica_pb2.Status.SUCCESS:
            logger.info(f"File deleted successfully with UUID {response.uuid} and version {response.timestamp} : {response.status}")
        else:
            logger.error(f"File not deleted successfully with UUID {response.uuid} and version {response.timestamp} : {response.status}")

    
def get_served():
    # TODO: add receiving logic
    # fetch replicas from registry server

    while True:
        # give user options of read write and delete
        logger.info(OPTIONS)
        try:
            choice = int(input("Enter your choice: "))
            if choice > 4 or choice < 1:
                raise ValueError
        except ValueError:
            logger.error("Invalid choice")
            continue
        except Exception as e:
            logger.critical("Something went wrong", e)
            exit(1)

        if choice == 1:
            # write
            # TODO: add write logic
            write_file(logger)
            
        elif choice == 2:
            # read
            # TODO: add read logic
            read_file(logger)
        elif choice == 3:
            # delete
            # TODO: add delete logic
            delete_file(logger)
            pass
        elif choice == 4:
            # exit
            logger.info("Exiting...")
            exit(0)


if __name__ == "__main__":
    # get sys args

    agr = argparse.ArgumentParser()
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

    logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    get_served()
