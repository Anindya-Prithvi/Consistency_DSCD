all:
	python -m grpc_tools.protoc -I ../protos --python_out=. --grpc_python_out=. registry_server.proto

test:
	@echo "Running test on Windows11, Write your own for other inferior platforms"
	@echo "To end test, please close the terminal instance"
	python registry_server.py&
	python community_server.py serber1 12000&
	python community_server.py serber2 12001&
	python community_server.py serber3 12002&
	python grpc_client-real.py
