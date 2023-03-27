import unittest
import multiprocessing
import logging
import sys

sys.path.append("../primary_backup")
logger = logging.getLogger("test")
logger.setLevel(logging.INFO)

class PBBP(unittest.TestCase):
    def test_launch_registry_server(self):
        from registry_server import serve
        p = multiprocessing.Process(target=serve, args=(logger, "[::1]", 1337))
        p.start()
        assert p.is_alive(), "Registry server not launched"
    def test_run_n_replicas(self):
        from blocking_server import serve
        processes = []
        n = int(input("How many replicas do you want to launch? "))
        for i in range(n):
            processes.append(multiprocessing.Process(target=serve, args=(logger, "[::1]:1337", f"test{i}er", "[::1]", 12000+i)))
        for p in processes:
            p.start()
        for p in processes:
            assert p.is_alive(), "Replica server not launched"

if __name__ == '__main__':
    unittest.main()