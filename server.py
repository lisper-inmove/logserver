# -*- coding: utf-8 -*-

import time
import socket
import select
import json
import os
import dotmap
import logging

from file_logger import FileLogger

class Server:
    def __init__(self, **kargs):

        config_path = kargs.get("config_path")
        self.connections = {}
        self.init_config(config_path)
        self.create_server()
        self.create_epoll()
        self.logger = FileLogger("LogServer").create()

    def init_config(self, config_path=None):
        current_dir = os.path.curdir
        if config_path is None:
            config_path = os.path.join(current_dir, "config.json")
        with open(config_path) as f:
            config = json.loads(f.read())
            self.config = dotmap.DotMap(config)

    def set_signal(self):
        pass

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

    def try_start(self):
        try:
            self.start()
        except Exception as ex:
            print("try_start exception: {}".format(ex))
            self.epoll.unregister(self.server.fileno())
            self.epoll.close()
            self.server.close()

    def start(self):
        self.logger.info("start server on port: {}".format(self.config.PORT))
        while True:
            time.sleep(1)
            events = self.epoll.poll(1)
            for fileno, event in events:
                if fileno == self.server.fileno():
                    conn, addr = self.server.accept()
                    conn.setblocking(0)
                    self.epoll.register(conn.fileno(), select.EPOLLIN)
                    self.connections.update({conn.fileno(): [conn, addr]})
                elif event & select.EPOLLIN:
                    data = self.connections[fileno][0].recv(self.config.MAX_DATA_SIZE)
                    self.deal_with_input(data, fileno)
                elif event & select.EPOLLOUT:
                    self.epoll.modify(fileno, 0)
                    self.connections[fileno][0].shutdown(socket.SHUT_RDWR)
                elif event & select.EPOLLHUP:
                    self.epoll.unregister(fileno)
                    self.connections[fileno][0].close()
                    del self.connections[fileno]

    def deal_with_input(self, data, fileno):
        self.epoll.modify(fileno, select.EPOLLOUT)
        print(data)

if __name__ == "__main__":
    pid = os.getpid()
    with open("server.pid", "w") as f:
        f.write(str(pid))
    server = Server()
    server.start()
