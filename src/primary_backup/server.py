# Any client can interact with any replica directly. There can be multiple clients
# concurrently interacting with the data store.

# Each file can be assumed to be very small in size ( 200-500 characters)


import uuid
import logging
import grpc
import argparse
import registry_server_pb2
import registry_server_pb2_grpc

_server_id = uuid.uuid4()  # private
logger = logging.getLogger(f"server-{str(_server_id)[:6]}")
logger.setLevel(logging.INFO)
LOGFILE = None  # default
REGISTRY_ADDR = "[::]:1337"
EXPOSE_IP = "[::]"
PORT = None
OPTIONS = """\
Please choose from the following options:
    1. WRITE
    2. READ
    3. DELETE
    4. EXIT\
"""


def serve():
    # TODO: server cleints
    pass


if __name__ == "__main__":
    # get sys args

    agr = argparse.ArgumentParser()
    agr.add_argument("--ip", type=str, help="ip address of server (default 0.0.0.0)", default="0.0.0.0")
    agr.add_argument("--port", type=int, help="port number", required=True)
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
    serve()
