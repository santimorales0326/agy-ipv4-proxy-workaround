import pathlib
import socket
import subprocess
import sys
import time
import unittest

PROXY = pathlib.Path(__file__).resolve().parents[1] / "proxy.py"


class ProxyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = subprocess.Popen(
            [sys.executable, str(PROXY), "--port", "18989"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        for _ in range(30):
            try:
                with socket.create_connection(("127.0.0.1", 18989), timeout=.2):
                    break
            except OSError:
                time.sleep(.05)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)

    def request(self, request):
        with socket.create_connection(("127.0.0.1", 18989), timeout=2) as conn:
            conn.sendall(request)
            return conn.recv(1024)

    def test_non_connect_rejected(self):
        self.assertIn(b"405", self.request(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n"))

    def test_non_https_port_rejected(self):
        self.assertIn(b"403", self.request(b"CONNECT example.com:80 HTTP/1.1\r\n\r\n"))


if __name__ == "__main__":
    unittest.main()
