all:
	python -m grpc_tools.protoc -I ../../../protos --python_out=. --grpc_python_out=. registry_server.proto replica.proto

clean:
	rm -r replicas
	rm -r __pycache__
	rm -r .ruff_cache