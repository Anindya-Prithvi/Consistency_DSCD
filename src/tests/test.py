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

if __name__ == '__main__':
    unittest.main()