# -*- coding: utf-8 -*-

import socket
import json
import time
import struct
import fcntl
import os

try:
    from file_logger import FileLogger
    logger = FileLogger("LogClient").create()
except:
    def logger():
        pass


class Client:
    def __init__(self, host=None, port=None, nonblock=True):
        if host is None:
            self.host = "127.0.0.1"
        if port is None:
            self.port = 6103
        self.nonblock = nonblock
        self.byte_order = "<" # little endian
        self.create_sock()

    def create_sock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        if self.nonblock:
            fcntl.fcntl(self.sock, fcntl.F_SETFL, os.O_NONBLOCK)

    def start(self):
        while True:
            data = input("输入你的内容: ")
            data = self.pack(data)
            start = time.time()
            self.sock.send(data)
            end = time.time()
            logger.info("发送数据耗时: {}".format(end - start))

    def pack(self, data):
        data = data.encode("utf8")
        length = len(data)
        data_format = "{}??".format(self.byte_order)
        return data

    def __del__(self):
        self.sock.close()

if "__main__" == __name__:
    client = Client()
    client.start()
