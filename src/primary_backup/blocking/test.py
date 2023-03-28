import shutil
import time
import unittest
import multiprocessing
import logging
import random
import sys
from time import sleep
import uuid

logger = logging.getLogger("test")
logger.setLevel(logging.INFO)



class PBBP(unittest.TestCase):
    n = 50
    process_list = []
    client_list = []
    client_files = [[]]

    def test01_launch_registry_server(self):
        # check path has blocking
        if sys.path[0].find("blocking") == -1: print("Not running from blocking directory")
        # running from project_dir/src/ (assumed pre-push)
        # so we need to add primary_blocking/blocking to sys.path
        if sys.path[-1] == "primary_backup/nonblocking":
            sys.path.pop()
        sys.path.append("primary_backup/blocking")
        from registry_server import serve

        p = multiprocessing.Process(target=serve, args=(logger, "[::1]", 1337))
        p.start()
        self.process_list.append(p)
        assert p.is_alive(), "Registry server not launched"
        # print return value of serve

        print("Waiting for registry server to come up...[2seconds]")
        sleep(2)

    def test02_run_n_replicas(self):
        from replica import serve

        processes = []
        # try:
        #     self.n = int(input("How many replicas do you want to launch? "))
        # except:
        #     print("Parse error, your fault, defaulting to 20 replicas")
        #     self.n = 20

        for i in range(self.n):
            processes.append(
                multiprocessing.Process(
                    target=serve,
                    args=(logger, "[::1]:1337", f"test{i}er", "[::1]", 12000 + i),
                )
            )
        for p in processes:
            p.start()
            self.process_list.append(p)
        for p in processes:
            assert p.is_alive(), "Replica server not launched"

        print("Waiting for all replicas to come up...[5seconds]")
        sleep(5)

    def test03_run_client(self):
        from client import Client

        c1 = Client(logger, "[::1]:1337")
        self.client_list.append(c1)
        assert (
            len(c1.KNOWN_SERVERS) == self.n
        ), f"All servers not up. Expected {self.n}, got {len(c1.KNOWN_SERVERS)}"

    def test04_run_client_write_one(self):
        # using first client
        c1 = self.client_list[0]
        replica = random.choice(c1.KNOWN_SERVERS)
        file_uuid = str(uuid.uuid4())
        filename = "I am Walter Hartwell White"
        content = "I live in Albuquerque, New Mexico. I am 51 years old. I have a wife and two children. I am a high school chemistry teacher. I have terminal lung cancer. I am also a methamphetamine manufacturer. I am the one who knocks."

        self.client_files[0].append((file_uuid, filename, content))

        st = time.time()
        resp = c1.write_to_replica(replica, file_uuid, filename, content)
        assert resp.status == "SUCCESS", "Write failed"
        assert resp.uuid == file_uuid, "UUID mismatch"
        assert len(resp.version) > 0, "Version not set"
        # can at most print resp.version, nothing to assert
        et = time.time()

        print(f"Write acknoledgement has been received within {et-st}")

    def test05_run_client_read_all(self):
        # using first client
        c1 = self.client_list[0]
        for replica in c1.KNOWN_SERVERS:
            resp = c1.read_from_replica(replica, self.client_files[0][0][0])
            # pretty stupid to write on stdout, but ok
            # print(resp)
            assert resp.status == "SUCCESS", "Write failed"
            assert (
                resp.name.find(self.client_files[0][0][1]) != -1
            ), f"Names don't match, Expected {self.client_files[0][0][1]} got {resp.name}"
            assert resp.content == self.client_files[0][0][2], f"content mismatch"
            assert len(resp.version) > 0, f"Version not set on replica {replica}"

    def test06_run_client_write_two(self):
        # using first client
        c1 = self.client_list[0]
        replica = random.choice(c1.KNOWN_SERVERS)
        file_uuid = str(uuid.uuid4())
        filename = "Mary on Cross"
        content = "...You go down just like Holy Mary, Mary on a, Mary on a cross Not just another bloody Mary, Mary on a, Mary on a cross. Your beauty never fai..."

        self.client_files[0].append((file_uuid, filename, content))

        st = time.time()
        resp = c1.write_to_replica(replica, file_uuid, filename, content)
        assert resp.status == "SUCCESS", "Write failed"
        assert resp.uuid == file_uuid, "UUID mismatch"
        assert len(resp.version) > 0, "Version not set"
        et = time.time()
        # can at most print resp.version, nothing to assert
        print(f"Write acknoledgement has been received within {et-st}")

    def test07_run_client_read_all(self):
        # using first client
        c1 = self.client_list[0]
        for replica in c1.KNOWN_SERVERS:
            resp = c1.read_from_replica(replica, self.client_files[0][1][0])
            # pretty stupid to write on stdout, but ok
            # print(resp)
            assert resp.status == "SUCCESS", "Write failed"
            assert resp.name.find(self.client_files[0][1][1]) != -1, "Name mismatch"
            assert (
                resp.content == self.client_files[0][1][2]
            ), f"Content mismatch on replica {replica}, expected {self.client_files[0][1][2]} got {resp.content}"
            assert len(resp.version) > 0, f"Version not set on replica {replica}"

    def test08_run_client_delete_one(self):
        # using first client
        c1 = self.client_list[0]
        replica = random.choice(c1.KNOWN_SERVERS)
        resp = c1.delete_from_replica(replica, self.client_files[0][0][0])

        assert resp.status == "SUCCESS", "Delete failed"
        # only fail SUCESS, nothing else to assert

    def test09_run_client_read_deleted(self):
        # using first client
        c1 = self.client_list[0]
        for replica in c1.KNOWN_SERVERS:
            resp = c1.read_from_replica(replica, self.client_files[0][0][0])
            # pretty stupid to write on stdout, but ok
            # print(resp)
            assert (
                resp.status == "FILE ALREADY DELETED"
            ), f"Read succeeded (this is bad), got {resp.status}"
            # everything else is empty

    def testzz_tear_down(self):
        for p in self.process_list:
            p.terminate()
            p.kill()
        assert not any(
            [p.is_alive() for p in self.process_list]
        ), "Processes not terminated"

        # also clean up replicas directory
        shutil.rmtree("replicas")
        # fin


if __name__ == "__main__":
    unittest.main()
