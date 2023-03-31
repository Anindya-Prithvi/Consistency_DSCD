import uuid
import logging
import grpc
import argparse
import registry_server_pb2, registry_server_pb2_grpc, replica_pb2, replica_pb2_grpc


class Client:
    def __init__(self, logger, REGISTRY_ADDR):
        self.logger = logger
        self.REGISTRY_ADDR = REGISTRY_ADDR
        self.OPTIONS = """\
Please choose from the following options:
    1. Write
    2. Read
    3. Delete
    ## utility options ##
    4. Print known UUIDs
    5. Print known servers
    6. Exit
"""
        response = self.client_get_replicas()
        self.KNOWN_SERVERS = (
            response.servers
        )  # critical anyways, error handling not done
        self.UUID_STORE = set()

    def write_to_replica(self, replica, file_uuid, filename, content):
        with grpc.insecure_channel(f"{replica.ip}:{replica.port}") as channel:
            stub = replica_pb2_grpc.ServeStub(channel)
            response = stub.Write(
                replica_pb2.FileObject(
                    uuid=file_uuid,
                    name=filename,
                    content=content,
                )
            )
            return response

    def read_from_replica(self, replica, file_uuid):
        with grpc.insecure_channel(f"{replica.ip}:{replica.port}") as channel:
            stub = replica_pb2_grpc.ServeStub(channel)
            response = stub.Read(
                replica_pb2.FileObject(
                    uuid=file_uuid,
                )
            )
            return response

    def client_get_replicas(self):
        with grpc.insecure_channel(self.REGISTRY_ADDR) as channel:
            stub = registry_server_pb2_grpc.MaintainStub(channel)
            response = stub.GetServerList(registry_server_pb2.Empty())
            return response

    def delete_from_replica(self, replica, file_uuid):
        with grpc.insecure_channel(f"{replica.ip}:{replica.port}") as channel:
            stub = replica_pb2_grpc.ServeStub(channel)
            response = stub.Delete(
                replica_pb2.FileObject(
                    uuid=file_uuid,
                )
            )
            return response

    def pretty_print_servers(self):
        for i, server in enumerate(self.KNOWN_SERVERS):
            print(f"{i+1}. {server.ip}:{server.port}")

    def print_options(self):
        print(self.OPTIONS)

    def print_UUID_STORE(self):
        print(self.UUID_STORE)


def get_served(logger, REGISTRY_ADDR):
    # fetch replicas from registry server
    # no need to do it again since no new replicas are assumed to be added

    # create client object
    client = Client(logger, REGISTRY_ADDR)

    while True:
        # give user options of read write and delete
        client.print_options()
        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            logger.error("Invalid choice")
            continue
        except Exception as e:
            logger.critical("Something went wrong", e)
            exit(1)

        if choice == 1:
            # write

            # choose a replica
            logger.info("Choose which replica to write to /^[0-9]+$/:")
            client.pretty_print_servers()
            try:
                replica = int(input())
                if replica > len(client.KNOWN_SERVERS) or replica < 1:
                    raise ValueError
                replica = client.KNOWN_SERVERS[replica - 1]
            except ValueError:
                logger.error("Invalid choice")
                continue

            # get a uuid
            logger.info("Enter UUID (Empty to generate new)")
            file_uuid = input().strip()

            # generate uuid
            if file_uuid == "":
                file_uuid = str(uuid.uuid4())
                client.UUID_STORE.add(file_uuid)

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

            response = client.write_to_replica(replica, file_uuid, filename, content)
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
            client.pretty_print_servers()
            try:
                replica = int(input())
                if replica > len(client.KNOWN_SERVERS) or replica < 1:
                    raise ValueError
                replica = client.KNOWN_SERVERS[replica - 1]
            except ValueError:
                logger.error("Invalid choice")
                continue

            # send to replica

            response = client.read_from_replica(replica, file_uuid)
            logger.info(f"Got response from replica {replica.ip}:{replica.port}")
            logger.info(f"Status: {response.status}")
            logger.info(f"Name: {response.name}")
            logger.info(f"Content: {response.content}")
            logger.info(f"Version: {response.version}")

        elif choice == 3:
            # delete

            # choose a replica
            logger.info("Choose which replica to delete from /^[0-9]+$/:")
            client.pretty_print_servers()
            try:
                replica = int(input())
                if replica > len(client.KNOWN_SERVERS) or replica < 1:
                    raise ValueError
                replica = client.KNOWN_SERVERS[replica - 1]
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
            response = client.delete_from_replica(replica, file_uuid)

            logger.info(f"Got response from replica {replica.ip}:{replica.port}")
            logger.info(f"Status: {response.status}")

        elif choice == 4:
            # print known uuids
            logger.info("Created UUIDs:")
            for uuid_i in client.UUID_STORE:
                print(uuid_i)
        elif choice == 5:
            # print known servers
            logger.info("Known servers:")
            client.pretty_print_servers()
        elif choice == 6:
            # exit
            logger.info("Exiting...")
            exit(0)


if __name__ == "__main__":
    # get sys args
    _client_id = uuid.uuid4()  # private
    logger = logging.getLogger(f"client-{str(_client_id)[:6]}")
    logger.setLevel(logging.INFO)
    LOGFILE = None  # default
    REGISTRY_ADDR = "[::1]:1337"

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
    get_served(logger, REGISTRY_ADDR)
