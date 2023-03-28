import unittest
import multiprocessing
import logging
import random
import sys
from time import sleep
import uuid

sys.path.append("../primary_backup")
logger = logging.getLogger("test")
logger.setLevel(logging.INFO)

class PBBP(unittest.TestCase):
    n=20
    process_list = []
    client_list = []
    client_files = [[]]
        
    def test01_launch_registry_server(self):
        from registry_server import serve
        p = multiprocessing.Process(target=serve, args=(logger, "[::1]", 1337))
        p.start()
        self.process_list.append(p)
        assert p.is_alive(), "Registry server not launched"
        # print return value of serve
        sleep(2)

    def test02_run_n_replicas(self):
        from blocking_server import serve
        processes = []
        # try:
        #     self.n = int(input("How many replicas do you want to launch? "))
        # except:
        #     print("Parse error, your fault, defaulting to 20 replicas")
        #     self.n = 20

        for i in range(self.n):
            processes.append(multiprocessing.Process(target=serve, args=(logger, "[::1]:1337", f"test{i}er", "[::1]", 12000+i)))
        for p in processes:
            p.start()
            self.process_list.append(p)
        for p in processes:
            assert p.is_alive(), "Replica server not launched"
        sleep(2)

    def test03_run_client(self):
        from client import Client
        c1 = Client(logger, "[::1]:1337")
        self.client_list.append(c1)
        assert len(c1.KNOWN_SERVERS)==self.n, "All Servers not reg. or client fail"
    
    def test04_run_client_write(self):
        # using first client
        c1 = self.client_list[0]
        replica = random.choice(c1.KNOWN_SERVERS)
        file_uuid = str(uuid.uuid4())
        filename = "I am Walter Hartwell White"
        content = "I live in Albuquerque, New Mexico. I am 51 years old. I have a wife and two children. I am a high school chemistry teacher. I have terminal lung cancer. I am also a methamphetamine manufacturer. I am the one who knocks."

        self.client_files[0].append((file_uuid, filename, content))

        resp = c1.write_to_replica(replica, file_uuid, filename, content)
        assert resp.status == "Success", "Write failed"
        assert resp.uuid == file_uuid, "UUID mismatch"
        assert len(resp.version)>0, "Version not set"
        # can at most print resp.version, nothing to assert
    
    def test05_run_client_read_all(self):
        # using first client
        c1 = self.client_list[0]
        for replica in c1.KNOWN_SERVERS:
            resp = c1.read_from_replica(replica, self.client_files[0][0][0])
            assert resp.status == "Success", "Write failed"
            assert resp.name == self.client_files[0][0][1]
            assert resp.content == self.client_files[0][0][2]
            assert len(resp.version)>0, f"Version not set on replica {replica}"


        
    
    def testzz_tear_down(self):
        for p in self.process_list:
            p.terminate()
            p.kill()
        assert not any([p.is_alive() for p in self.process_list]), "Processes not terminated"

if __name__ == '__main__':
    unittest.main()