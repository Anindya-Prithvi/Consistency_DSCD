# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import quorum_registry_pb2 as quorum__registry__pb2
import quorum_replica_pb2 as quorum__replica__pb2


class PrimeraStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RecvReplica = channel.unary_unary(
                '/Primera/RecvReplica',
                request_serializer=quorum__registry__pb2.Server_information.SerializeToString,
                response_deserializer=quorum__registry__pb2.Success.FromString,
                )


class PrimeraServicer(object):
    """Missing associated documentation comment in .proto file."""

    def RecvReplica(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PrimeraServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RecvReplica': grpc.unary_unary_rpc_method_handler(
                    servicer.RecvReplica,
                    request_deserializer=quorum__registry__pb2.Server_information.FromString,
                    response_serializer=quorum__registry__pb2.Success.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Primera', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Primera(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def RecvReplica(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Primera/RecvReplica',
            quorum__registry__pb2.Server_information.SerializeToString,
            quorum__registry__pb2.Success.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class ServeStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Write = channel.unary_unary(
                '/Serve/Write',
                request_serializer=quorum__replica__pb2.FileObject.SerializeToString,
                response_deserializer=quorum__replica__pb2.FileObject.FromString,
                )
        self.Read = channel.unary_unary(
                '/Serve/Read',
                request_serializer=quorum__replica__pb2.FileObject.SerializeToString,
                response_deserializer=quorum__replica__pb2.FileObject.FromString,
                )
        self.Delete = channel.unary_unary(
                '/Serve/Delete',
                request_serializer=quorum__replica__pb2.FileObject.SerializeToString,
                response_deserializer=quorum__replica__pb2.FileObject.FromString,
                )


class ServeServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Write(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Read(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Delete(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ServeServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Write': grpc.unary_unary_rpc_method_handler(
                    servicer.Write,
                    request_deserializer=quorum__replica__pb2.FileObject.FromString,
                    response_serializer=quorum__replica__pb2.FileObject.SerializeToString,
            ),
            'Read': grpc.unary_unary_rpc_method_handler(
                    servicer.Read,
                    request_deserializer=quorum__replica__pb2.FileObject.FromString,
                    response_serializer=quorum__replica__pb2.FileObject.SerializeToString,
            ),
            'Delete': grpc.unary_unary_rpc_method_handler(
                    servicer.Delete,
                    request_deserializer=quorum__replica__pb2.FileObject.FromString,
                    response_serializer=quorum__replica__pb2.FileObject.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Serve', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Serve(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Write(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Serve/Write',
            quorum__replica__pb2.FileObject.SerializeToString,
            quorum__replica__pb2.FileObject.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Read(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Serve/Read',
            quorum__replica__pb2.FileObject.SerializeToString,
            quorum__replica__pb2.FileObject.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Delete(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Serve/Delete',
            quorum__replica__pb2.FileObject.SerializeToString,
            quorum__replica__pb2.FileObject.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class BackupStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.WriteBackup = channel.unary_unary(
                '/Backup/WriteBackup',
                request_serializer=quorum__replica__pb2.FileObject.SerializeToString,
                response_deserializer=quorum__registry__pb2.Success.FromString,
                )
        self.DeleteBackup = channel.unary_unary(
                '/Backup/DeleteBackup',
                request_serializer=quorum__replica__pb2.FileObject.SerializeToString,
                response_deserializer=quorum__registry__pb2.Success.FromString,
                )


class BackupServicer(object):
    """Missing associated documentation comment in .proto file."""

    def WriteBackup(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteBackup(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_BackupServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'WriteBackup': grpc.unary_unary_rpc_method_handler(
                    servicer.WriteBackup,
                    request_deserializer=quorum__replica__pb2.FileObject.FromString,
                    response_serializer=quorum__registry__pb2.Success.SerializeToString,
            ),
            'DeleteBackup': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteBackup,
                    request_deserializer=quorum__replica__pb2.FileObject.FromString,
                    response_serializer=quorum__registry__pb2.Success.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Backup', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Backup(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def WriteBackup(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Backup/WriteBackup',
            quorum__replica__pb2.FileObject.SerializeToString,
            quorum__registry__pb2.Success.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DeleteBackup(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Backup/DeleteBackup',
            quorum__replica__pb2.FileObject.SerializeToString,
            quorum__registry__pb2.Success.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
