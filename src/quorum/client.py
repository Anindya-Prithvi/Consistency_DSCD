import datetime
import uuid
import logging
import grpc
import argparse
import quorum_registry_pb2, quorum_registry_pb2_grpc, quorum_replica_pb2, quorum_replica_pb2_grpc


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
    6. Ask Registry for write replicas
    7. Ask Registry for read replicas
    8. Ask for all replicas [debug]
    9. Exit
"""
        self.UUID_STORE = set()

    def get_write_replicas(self):
        with grpc.insecure_channel(self.REGISTRY_ADDR) as channel:
            stub = quorum_registry_pb2_grpc.MaintainStub(channel)
            response = stub.GetWriteReplicas(quorum_registry_pb2.Empty())
            self.nw = response
            return response

    def get_read_replicas(self):
        with grpc.insecure_channel(self.REGISTRY_ADDR) as channel:
            stub = quorum_registry_pb2_grpc.MaintainStub(channel)
            response = stub.GetReadReplicas(quorum_registry_pb2.Empty())
            self.nr = response
            return response

    def get_all_replicas(self):
        with grpc.insecure_channel(self.REGISTRY_ADDR) as channel:
            stub = quorum_registry_pb2_grpc.MaintainStub(channel)
            response = stub.GetAllReplicas(quorum_registry_pb2.Empty())
            self.n = response
            return response

    def write_to_replica(self, replica, file_uuid, filename, content):
        with grpc.insecure_channel(f"{replica.ip}:{replica.port}") as channel:
            stub = quorum_replica_pb2_grpc.ServeStub(channel)
            response = stub.Write(
                quorum_replica_pb2.FileObject(
                    uuid=file_uuid,
                    name=filename,
                    content=content,
                )
            )
            return response

    def read_from_replica(self, replica, file_uuid):
        with grpc.insecure_channel(f"{replica.ip}:{replica.port}") as channel:
            stub = quorum_replica_pb2_grpc.ServeStub(channel)
            response = stub.Read(
                quorum_replica_pb2.FileObject(
                    uuid=file_uuid,
                )
            )
            return response

    def delete_from_replica(self, replica, file_uuid):
        with grpc.insecure_channel(f"{replica.ip}:{replica.port}") as channel:
            stub = quorum_replica_pb2_grpc.ServeStub(channel)
            response = stub.Delete(
                quorum_replica_pb2.FileObject(
                    uuid=file_uuid,
                )
            )
            return response

    def write_to_replicas(self, replicas, file_uuid, filename, content):
        responses = []
        # Why randomising everytime?
        for replica in replicas:
            responses.append(self.write_to_replica(replica, file_uuid, filename, content))
        return responses

    def read_from_replicas(self, replicas, file_uuid):
        latest_response = None
        latest_version = datetime.datetime.min
        for i,replica in enumerate(replicas):
            resp = self.read_from_replica(replica, file_uuid)
            if i==0:
                latest_response = resp # to save null response
            # compare version
            # parse version of resp "%d/%m/%Y %H:%M:%S"
            if resp.status != "SUCCESS":
                continue
            version = datetime.datetime.strptime(resp.version, "%d/%m/%Y %H:%M:%S")
            if version > latest_version:
                latest_version = version
                latest_response = resp
        return latest_response

    def delete_from_replicas(self, replicas, file_uuid):
        responses = []
        for replica in replicas:
            responses.append(self.delete_from_replica(replica, file_uuid))
        return responses

    def pretty_print_servers(self, serverlist):
        for i, server in enumerate(serverlist):
            print(f"{i+1}. {server.ip}:{server.port}")

    def print_options(self):
        print(self.OPTIONS)

    def print_UUID_STORE(self):
        print(self.UUID_STORE)


def get_served(logger, REGISTRY_ADDR, OPTIONS):
    # fetch replicas from registry server
    # no need to do it again since no new replicas are assumed to be added

    # create client object
    client = Client(logger, REGISTRY_ADDR, OPTIONS)
    #TODO: Rewrite interaction

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

            # choose a replica
            # logger.info("Choose which replica to write to /^[0-9]+$/:")
            
            # get write replica and print them
            server_list = client.get_write_replicas().servers
            client.pretty_print_servers(server_list)
            # try:
            #     replica = int(input())
            #     if replica > len(server_list) or replica < 1:
            #         raise ValueError
            #     replica = server_list[replica - 1]
            # except ValueError:
            #     logger.error("Invalid choice")
            #     continue

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

            # send to replicas

            response = client.write_to_replicas(server_list, file_uuid, filename, content)
            for resp in response:
                # logger.info(f"Got response from replica {replica.ip}:{replica.port}")
                logger.info(f"Status: {resp.status}")
                logger.info(f"UUID: {resp.uuid}")
                logger.info(f"Version: {resp.version}")

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
            # logger.info("Choose which replica to read from /^[0-9]+$/:")

            # get read replicas and print them
            server_list = client.get_read_replicas().servers
            client.pretty_print_servers(server_list)
            # try:
            #     replica = int(input())
            #     if replica > len(client.KNOWN_SERVERS) or replica < 1:
            #         raise ValueError
            #     replica = client.KNOWN_SERVERS[replica - 1]
            # except ValueError:
            #     logger.error("Invalid choice")
            #     continue


            response = client.read_from_replicas(server_list, file_uuid)
            for resp in response:
                # logger.info(f"Got response from replica {replica.ip}:{replica.port}")
                logger.info(f"Status: {resp.status}")
                logger.info(f"Name: {resp.name}")
                logger.info(f"Content: {resp.content}")
                logger.info(f"Version: {resp.version}")

        elif choice == 3:
            # delete

            # choose a replica
            # logger.info("Choose which replica to delete from /^[0-9]+$/:")

            server_list = client.get_write_replicas().servers
            client.pretty_print_servers(server_list)
            # try:
            #     replica = int(input())
            #     if replica > len(client.KNOWN_SERVERS) or replica < 1:
            #         raise ValueError
            #     replica = client.KNOWN_SERVERS[replica - 1]
            # except ValueError:
            #     logger.error("Invalid choice")
            #     continue

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
            response = client.delete_from_replicas(server_list, file_uuid)
            for resp in response:
                # logger.info(f"Got response from replica {replica.ip}:{replica.port}")
                logger.info(f"Status: {resp.status}")

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
            # Ask registry for write replicas
            logger.info("Write replicas:")
            client.pretty_print_servers(client.nw.servers)
        elif choice == 7:
            # Ask registry for read replicas
            logger.info("Read replicas:")
            client.pretty_print_servers(client.nr.servers)
        elif choice == 8:
            # Ask registry for all replicas
            logger.info("All replicas:")
            client.pretty_print_servers(client.get_all_replicas().servers)
        elif choice == 9:
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
