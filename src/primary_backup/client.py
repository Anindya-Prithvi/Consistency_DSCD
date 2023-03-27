import uuid
import logging
import grpc
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
    1. Write
    2. Read
    3. Delete
    ## utility options ##
    4. Print known UUIDs
    5. Print known servers
    6. Exit
"""
KNOWN_SERVERS = set()
UUID_STORE = set()

def pretty_print_servers(servers):
    for i, server in enumerate(servers):
        print(f"{i+1}. {server.ip}:{server.port}")


def get_served():
    global KNOWN_SERVERS, UUID_STORE
    # fetch replicas from registry server
    # no need to do it again since no new replicas are assumed to be added
    with grpc.insecure_channel(REGISTRY_ADDR) as channel:
        stub = registry_server_pb2_grpc.MaintainStub(channel)
        response = stub.GetServerList(registry_server_pb2.Empty())
        logger.info(f"Got server list from registry server")
        
        KNOWN_SERVERS = set(response.servers)

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

            #choose a replica
            logger.info("Choose which replica to write to /^[0-9]+$/:")
            pretty_print_servers(KNOWN_SERVERS)
            try:
                replica = int(input())
                if replica > len(KNOWN_SERVERS) or replica < 1:
                    raise ValueError
                replica = KNOWN_SERVERS[replica-1]
            except ValueError:
                logger.error("Invalid choice")
                continue
            
            # get a uuid
            logger.info("Enter UUID (Empty to generate new)")
            file_uuid = input().strip()

            # generate uuid
            if file_uuid == "":
                file_uuid = str(uuid.uuid4())
                UUID_STORE.add(file_uuid)

            # validate uuid
            try:
                uuid.UUID(file_uuid)
            except ValueError:
                logger.error("Invalid UUID")
                continue
            
            # get filename
            logger.info("Enter filename")
            filename = input()

            # get file content
            logger.info("Enter file content")
            content = input()

            # send to replica
            with grpc.insecure_channel(f"{replica.ip}:{replica.port}") as channel:
                stub = replica_pb2_grpc.ServeStub(channel)
                response = stub.Write(
                    replica_pb2.FileObject(
                        uuid=file_uuid,
                        name=filename,
                        content=content,
                    )
                )
                logger.info(f"Got response from replica {replica.ip}:{replica.port}")
                logger.info(f"Status: {response.status}")
                logger.info(f"UUID: {response.uuid}")
                logger.info(f"Version: {response.version}")

            
        elif choice == 2:
            # read
            logger.info("Enter UUID (Required)")
            file_uuid = input().strip()

            # validate uuid
            try:
                uuid.UUID(file_uuid)
            except ValueError:
                logger.error("Invalid UUID")
                continue

            # choose a replica
            logger.info("Choose which replica to read from /^[0-9]+$/:")
            pretty_print_servers(KNOWN_SERVERS)
            try:
                replica = int(input())
                if replica > len(KNOWN_SERVERS) or replica < 1:
                    raise ValueError
                replica = KNOWN_SERVERS[replica-1]
            except ValueError:
                logger.error("Invalid choice")
                continue

            # send to replica
            with grpc.insecure_channel(f"{replica.ip}:{replica.port}") as channel:
                stub = replica_pb2_grpc.ServeStub(channel)
                response = stub.Read(
                    replica_pb2.FileObject(
                        uuid=file_uuid,
                    )
                )
                logger.info(f"Got response from replica {replica.ip}:{replica.port}")
                logger.info(f"Status: {response.status}")
                logger.info(f"Name: {response.name}")
                logger.info(f"Content: {response.content}")
                logger.info(f"Version: {response.version}")
            
        elif choice == 3:
            # delete
            
            # choose a replica
            logger.info("Choose which replica to delete from /^[0-9]+$/:")
            pretty_print_servers(KNOWN_SERVERS)
            try:
                replica = int(input())
                if replica > len(KNOWN_SERVERS) or replica < 1:
                    raise ValueError
                replica = KNOWN_SERVERS[replica-1]
            except ValueError:
                logger.error("Invalid choice")
                continue

            # get a uuid
            logger.info("Enter UUID (Required)")
            file_uuid = input().strip()
            
            # validate uuid
            try:
                uuid.UUID(file_uuid)
            except ValueError:
                logger.error("Invalid UUID")
                continue

            # send to replica
            with grpc.insecure_channel(f"{replica.ip}:{replica.port}") as channel:
                stub = replica_pb2_grpc.ServeStub(channel)
                response = stub.Delete(
                    replica_pb2.FileObject(
                        uuid=file_uuid,
                    )
                )
                logger.info(f"Got response from replica {replica.ip}:{replica.port}")
                logger.info(f"Status: {response.status}")

        elif choice == 4:
            # print known uuids
            logger.info("Created UUIDs:")
            for uuid in UUID_STORE:
                print(uuid)
        elif choice == 5:
            # print known servers
            logger.info("Known servers:")
            pretty_print_servers(KNOWN_SERVERS)
        elif choice == 6:
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
