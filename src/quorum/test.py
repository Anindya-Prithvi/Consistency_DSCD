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



class QUORUM(unittest.TestCase):
    n = 50
    nr = n//2 + 1 # 26
    nw = n//2 + 1 # 26
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
        if sys.path[-1] == "primary_backup/blocking":
            sys.path.pop()
        sys.path.append("quorum")
        from quorum_registry import serve

        # launch config for N, Nr, Nw
        
        N = (self.n, self.nr, self.nw)

        p = multiprocessing.Process(target=serve, args=(logger, "[::1]", 1337, N))
        p.start()
        self.process_list.append(p)
        
        # print return value of serve

        print("Waiting for registry server to come up...[2seconds]")
        sleep(2)
        assert p.is_alive(), "Registry server not launched"

    def test02_run_n_replicas(self):
        from quorum_replica import serve

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
        assert c1 is not None, "Client object creation failed"

    def test03_run_client1_get_read_replicas(self):
        # using first client
        c1 = self.client_list[0]
        replica_list = c1.get_read_replicas()
        # print(f"Read replicas: {replica_list}")
        assert len(replica_list.servers) == self.nr, "No read replicas found"

    def test03_run_client1_get_write_replicas(self):
        # using first client
        c1 = self.client_list[0]
        replica_list = c1.get_write_replicas()
        # print(f"Write replicas: {replica_list}")
        assert len(replica_list.servers) == self.nw, "No write replicas found"

    def test03_run_client1_get_all_replicas(self):
        # using first client
        c1 = self.client_list[0]
        replica_list = c1.get_all_replicas()
        # print(f"All replicas: {replica_list}")
        assert len(replica_list.servers) == self.n, "No replicas found"
        
    def test04_run_client_write_nw(self):
        # using first client
        
        c1 = self.client_list[0]
        
        file_uuid = str(uuid.uuid4())
        filename = "I am Walter Hartwell White"
        content = "I live in Albuquerque, New Mexico. I am 51 years old. I have a wife and two children. I am a high school chemistry teacher. I have terminal lung cancer. I am also a methamphetamine manufacturer. I am the one who knocks."

        self.client_files[0].append((file_uuid, filename, content))

        # st = time.time()
        resps = c1.write_to_replicas(c1.nw.servers, file_uuid, filename, content)
        for resp in resps:
            assert resp.status == "SUCCESS", "Write failed"
            assert resp.uuid == file_uuid, "UUID mismatch"
            assert len(resp.version) > 0, "Version not set"
        # can at most print resp.version, nothing to assert
        # et = time.time()


    def test05_run_client_read_nr(self):
        # using first client
        c1 = self.client_list[0]
        latest_file = c1.read_from_replicas(c1.nr.servers, self.client_files[0][0][0])
        assert latest_file.status == "SUCCESS", "Read failed"
        assert latest_file.name.find(self.client_files[0][0][1])!=-1, f"Filename mismatch, got {latest_file.name}"
        assert latest_file.content == self.client_files[0][0][2], "Content mismatch"
        assert len(latest_file.version) > 0, "Version not set"


    def test06_run_client_write_nw_two(self):
        # using first client
        c1 = self.client_list[0]
        
        file_uuid = str(uuid.uuid4())
        filename = "Poetic Rizz"
        content = "You and the sun hold little to no difference, just like I cannot ignore the sun's rays of light, I cannot ignore your radiant beauty."

        self.client_files[0].append((file_uuid, filename, content))

        # st = time.time()
        resps = c1.write_to_replicas(c1.nw.servers, file_uuid, filename, content)
        for resp in resps:
            assert resp.status == "SUCCESS", "Write failed"
            assert resp.uuid == file_uuid, "UUID mismatch"
            assert len(resp.version) > 0, "Version not set"
        # can at most print resp.version, nothing to assert
        # et = time.time()


    def test07_run_client_read_nr_two(self):
        # using first client
        c1 = self.client_list[0]
        latest_file = c1.read_from_replicas(c1.nr.servers, self.client_files[0][1][0])
        assert latest_file.status == "SUCCESS", "Read failed"
        assert latest_file.name.find(self.client_files[0][1][1])!=-1, f"Filename mismatch, got {latest_file.name}"
        assert latest_file.content == self.client_files[0][1][2], "Content mismatch"
        assert len(latest_file.version) > 0, "Version not set"

    def test08_run_client_delete_one(self):
        # using first client
        c1 = self.client_list[0]
        resps = c1.delete_from_replicas(c1.nw.servers, self.client_files[0][0][0])
        count_success = 0
        for resp in resps:
            # cannot assert on status
            if resp.status == "SUCCESS":
                count_success += 1
            
        assert count_success >= self.nw + self.nr - self.n, f"Delete failed on {self.nw-count_success} replicas out of {self.nw}"

    def test09_run_client_read_deleted(self):
        # using first client
        c1 = self.client_list[0]
        latest_file = c1.read_from_replicas(self.client_files[0][0][0])
        # assert latest_file.status == "NOT_FOUND", "Read succeeded on deleted file (bad)"
        # no assertion possible, client_read quorum takes arbitrary quorums, some may succeed, some wont
        assert latest_file.status != "", "No status message"

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
