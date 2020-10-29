# -*- coding: utf-8 -*-

import socket
import json
import time
import struct
import fcntl, os

class Client:
    def __init__(self, host=None, port=None):
        if host is None:
            self.host = "127.0.0.1"
        if port is None:
            self.port = 6103
        self.create_sock()

    def create_sock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        fcntl.fcntl(self.sock, fcntl.F_SETFL, os.O_NONBLOCK)

    def start(self):
        while True:
            data = input("输入你的内容: ")
            # data = json.dumps(data)
            data = data * 10000000
            data = data.encode("utf8")
            start = time.time()
            self.sock.send(data)
            end = time.time()
            print("发送耗时: {}".format(end - start))

    def __del__(self):
        self.sock.close()

if "__main__" == __name__:
    client = Client()
    client.start()
