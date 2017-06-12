#!/usr/bin/env pytho
import socket
import json

if "__main__" == __name__:
    for x in xrange(1, 2):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        sock.connect(('127.0.0.1', 8003));
        data = [[1, 1002, "2015-01-01", "192.168.10.219", "this is a test"]]
        sock.send(json.dumps(data));

        #szBuf = sock.recv(2048);
        sock.close();

        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        #sock.connect(('127.0.0.1', 8003));
        #data = [2, 9999, "2015-01-01", "192.168.10.219", {"answer": "this is a test"}]
        #sock.send(json.dumps(data))
        #sock.close();
    print("end of connect");
