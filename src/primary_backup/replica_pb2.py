# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: replica.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import registry_server_pb2 as registry__server__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\rreplica.proto\x1a\x15registry_server.proto"\xa8\x01\n\nFileObject\x12\x13\n\x06status\x18\x01 \x01(\tH\x00\x88\x01\x01\x12\x11\n\x04uuid\x18\x02 \x01(\tH\x01\x88\x01\x01\x12\x14\n\x07version\x18\x03 \x01(\tH\x02\x88\x01\x01\x12\x14\n\x07\x63ontent\x18\x04 \x01(\tH\x03\x88\x01\x01\x12\x11\n\x04name\x18\x05 \x01(\tH\x04\x88\x01\x01\x42\t\n\x07_statusB\x07\n\x05_uuidB\n\n\x08_versionB\n\n\x08_contentB\x07\n\x05_name27\n\x07Primera\x12,\n\x0bRecvReplica\x12\x13.Server_information\x1a\x08.Success2v\n\x05Serve\x12#\n\x05Write\x12\x0b.FileObject\x1a\x0b.FileObject"\x00\x12"\n\x04Read\x12\x0b.FileObject\x1a\x0b.FileObject"\x00\x12$\n\x06\x44\x65lete\x12\x0b.FileObject\x1a\x0b.FileObject"\x00\x32Y\n\x06\x42\x61\x63kup\x12&\n\x0bWriteBackup\x12\x0b.FileObject\x1a\x08.Success"\x00\x12\'\n\x0c\x44\x65leteBackup\x12\x0b.FileObject\x1a\x08.Success"\x00\x62\x06proto3'
)

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "replica_pb2", globals())
if _descriptor._USE_C_DESCRIPTORS == False:
    DESCRIPTOR._options = None
    _FILEOBJECT._serialized_start = 41
    _FILEOBJECT._serialized_end = 209
    _PRIMERA._serialized_start = 211
    _PRIMERA._serialized_end = 266
    _SERVE._serialized_start = 268
    _SERVE._serialized_end = 386
    _BACKUP._serialized_start = 388
    _BACKUP._serialized_end = 477
# @@protoc_insertion_point(module_scope)
