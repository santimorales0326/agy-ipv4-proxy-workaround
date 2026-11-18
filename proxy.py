#!/usr/bin/env python3
"""Local-only HTTPS CONNECT proxy with IPv4-only upstream connections."""
import argparse
import logging
import select
import socket
import socketserver

LOG = logging.getLogger("agy-ipv4-proxy")
MAX_HEADER = 16384


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        client = self.request
        client.settimeout(15)
        data = b""
        try:
            while b"\r\n\r\n" not in data:
                chunk = client.recv(4096)
                if not chunk or len(data) + len(chunk) > MAX_HEADER:
                    return
                data += chunk

            header, extra = data.split(b"\r\n\r\n", 1)
            method, target, _ = header.split(b"\r\n", 1)[0].decode("ascii").split(" ", 2)
            if method != "CONNECT":
                client.sendall(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n")
                return
            host, port_text = target.rsplit(":", 1)
            if not host or not port_text.isdecimal() or int(port_text) != 443:
                client.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
                return

            upstream = None
            for family, kind, proto, _, address in socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM):
                candidate = socket.socket(family, kind, proto)
                try:
                    candidate.settimeout(10)
                    candidate.connect(address)
                    upstream = candidate
                    break
                except OSError:
                    candidate.close()
            if upstream is None:
                client.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
                return

            with upstream:
                client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                if extra:
                    upstream.sendall(extra)
                client.settimeout(None)
                upstream.settimeout(None)
                sockets = (client, upstream)
                while True:
                    ready, _, _ = select.select(sockets, [], [], 120)
                    if not ready:
                        return
                    for source in ready:
                        payload = source.recv(65536)
                        if not payload:
                            return
                        (upstream if source is client else client).sendall(payload)
        except (OSError, ValueError, UnicodeError) as exc:
            LOG.debug("Tunnel ended: %s", exc)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18888)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    with Server(("127.0.0.1", args.port), Handler) as server:
        LOG.info("IPv4-only CONNECT proxy listening on 127.0.0.1:%s", args.port)
        server.serve_forever()


if __name__ == "__main__":
    main()
