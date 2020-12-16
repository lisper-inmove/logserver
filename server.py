# -*- coding: utf-8 -*-

import socket
import select
import json
import os
import dotmap


class Server:
    def __init__(self, **kargs):

        config_path = kargs.get("config_path")
        self.connections = {}
        self.init_config(config_path)
        self.create_server()
        self.create_epoll()

    def init_config(self, config_path=None):
        current_dir = os.path.curdir
        if config_path is None:
            config_path = os.path.join(current_dir, "config.json")
        with open(config_path) as f:
            config = json.loads(f.read())
            self.config = dotmap.DotMap(config)

    def create_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.config.HOST, self.config.PORT))
        self.server.listen(self.config.MAX_CONN)
        self.server.setblocking(0)
        self.server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def create_epoll(self):
        self.epoll = select.epoll()
        self.epoll.register(self.server.fileno(), select.EPOLLIN)

    def start(self):
        while True:
            events = self.epoll.poll(1)
            for fileno, event in events:
                if fileno == self.server.fileno():
                    conn, addr = self.server.accept()
                    conn.setblocking(0)
                    self.epoll.register(conn.fileno(), select.EPOLLIN)
                    self.connections.update({fileno: [conn, addr]})
                elif event & select.EPOLLIN:
                    data = self.connections[fileno][0].recv(self.config.MAX_DATA_SIZE)
                    if len(data) <= 0:
                        self.epoll.modify(fileno, select.EPOLLOUT)
                    self.epoll.modify(fileno, select.EPOLLOUT)
                    print("get data: {}".format(data))
                elif event & select.EPOLLOUT:
                    self.epoll.modify(fileno, 0)
                    self.connections[fileno][0].shutdown(socket.SHUT_RDWR)
                elif event & select.EPOLLHUP:
                    self.epoll.unregister(fileno)
                    self.connections[fileno][0].close()
                    del self.connections[fileno]


if __name__ == "__main__":
    pid = os.getpid()
    with open("server.pid", "w") as f:
        f.write(str(pid))
    server = Server()
    server.start()
