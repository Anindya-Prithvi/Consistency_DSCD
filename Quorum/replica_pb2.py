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




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rreplica.proto\"i\n\rClientRequest\x12\x11\n\x04name\x18\x01 \x01(\tH\x00\x88\x01\x01\x12\x14\n\x07\x63ontent\x18\x02 \x01(\tH\x01\x88\x01\x01\x12\x11\n\x04uuid\x18\x03 \x01(\tH\x02\x88\x01\x01\x42\x07\n\x05_nameB\n\n\x08_contentB\x07\n\x05_uuid\"\xb1\x01\n\x0fReplicaResponse\x12\x13\n\x06status\x18\x01 \x01(\x08H\x00\x88\x01\x01\x12\x11\n\x04uuid\x18\x02 \x01(\tH\x01\x88\x01\x01\x12\x16\n\ttimestamp\x18\x03 \x01(\tH\x02\x88\x01\x01\x12\x14\n\x07\x63ontent\x18\x04 \x01(\tH\x03\x88\x01\x01\x12\x11\n\x04name\x18\x05 \x01(\tH\x04\x88\x01\x01\x42\t\n\x07_statusB\x07\n\x05_uuidB\x0c\n\n_timestampB\n\n\x08_contentB\x07\n\x05_name2\x8e\x01\n\x05Serve\x12+\n\x05Write\x12\x0e.ClientRequest\x1a\x10.ReplicaResponse\"\x00\x12*\n\x04Read\x12\x0e.ClientRequest\x1a\x10.ReplicaResponse\"\x00\x12,\n\x06\x44\x65lete\x12\x0e.ClientRequest\x1a\x10.ReplicaResponse\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'replica_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CLIENTREQUEST._serialized_start=17
  _CLIENTREQUEST._serialized_end=122
  _REPLICARESPONSE._serialized_start=125
  _REPLICARESPONSE._serialized_end=302
  _SERVE._serialized_start=305
  _SERVE._serialized_end=447
# @@protoc_insertion_point(module_scope)
