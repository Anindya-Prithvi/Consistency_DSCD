# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: quorum_registry.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15quorum_registry.proto\"H\n\x12Server_information\x12\x0f\n\x02ip\x18\x01 \x01(\tH\x00\x88\x01\x01\x12\x11\n\x04port\x18\x02 \x01(\tH\x01\x88\x01\x01\x42\x05\n\x03_ipB\x07\n\x05_port\",\n\x12\x43lient_information\x12\x0f\n\x02id\x18\x01 \x01(\tH\x00\x88\x01\x01\x42\x05\n\x03_id\"\'\n\x07Success\x12\x12\n\x05value\x18\x01 \x01(\x08H\x00\x88\x01\x01\x42\x08\n\x06_value\"3\n\x0bServer_book\x12$\n\x07servers\x18\x01 \x03(\x0b\x32\x13.Server_information\"\x07\n\x05\x45mpty2\xb6\x01\n\x08Maintain\x12/\n\x0eRegisterServer\x12\x13.Server_information\x1a\x08.Success\x12&\n\x0eGetAllReplicas\x12\x06.Empty\x1a\x0c.Server_book\x12(\n\x10GetWriteReplicas\x12\x06.Empty\x1a\x0c.Server_book\x12\'\n\x0fGetReadReplicas\x12\x06.Empty\x1a\x0c.Server_bookb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'quorum_registry_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _SERVER_INFORMATION._serialized_start=25
  _SERVER_INFORMATION._serialized_end=97
  _CLIENT_INFORMATION._serialized_start=99
  _CLIENT_INFORMATION._serialized_end=143
  _SUCCESS._serialized_start=145
  _SUCCESS._serialized_end=184
  _SERVER_BOOK._serialized_start=186
  _SERVER_BOOK._serialized_end=237
  _EMPTY._serialized_start=239
  _EMPTY._serialized_end=246
  _MAINTAIN._serialized_start=249
  _MAINTAIN._serialized_end=431
# @@protoc_insertion_point(module_scope)
