# -*- coding: utf-8 -*-

import socket, select ,json ,datetime ,os, sys ,Queue ,signal
reload(sys)
sys.setdefaultencoding("utf-8")

class V:
    config_file = "config.json"
    host = "HOST"
    port = "PORT"
    max_conn = "MAX_CONN"
    max_data_size = "MAX_DATA_SIZE"
    log_path = "LOG_PATH"
    applications = "applications"
    queue_size = "queue_size"
    logfile = "log_file.log" # logserver的日志存放
    name = "V.name"

    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"

class Server:
    def __init__(self, **kargs):
        config = None
        with open(V.config_file) as f:
            config = json.loads(f.read())
        self._host = config.get(V.host)
        self._port = config.get(V.port)
        self._max_conn = config.get(V.max_conn)
        self._max_data_size = config.get(V.max_data_size)
        self.path = config.get(V.log_path)
        if not os.path.exists(self.path):
            print "%s not exists" % (self.path)
            sys.exit()
        self.applications = config.get(V.applications)
        self.lvs = [V.error, V.warning, V.info, V.debug]
        self.fds = {}
        self._logQueue = Queue.Queue(config.get(V.queue_size))
    def __setitem__(self, k, v):
        self.__dict__[k] = v
    def __getitem__(self, k):
        return self.__dict__.get(k, None)

    def start(self, **kargs):
        _server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _server_sock.bind((self._host, self._port))
        _server_sock.listen(self._max_conn)
        _server_sock.setblocking(0)
        _server_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        _epoll = select.epoll()
        _epoll.register(_server_sock.fileno(), select.EPOLLIN)
        _connections = {}
        _f1 = open(V.logfile, "a", 1)
        # 重新加载配置文件
        signal.signal(signal.SIGUSR1, self.__reload_config)
        # 清空日志队列,日志堆积时使用,防止服务器down机
        signal.signal(signal.SIGUSR2, self.__jeter_log)

        try:
            while True:
                try:
                    _events = _epoll.poll(1)
                    self.log()
                    for fileno, event in _events:
                        if fileno == _server_sock.fileno(): # _server_sock绑定的事件到达
                            _conn, _addr = _server_sock.accept()
                            _conn.setblocking(0)
                            _epoll.register(_conn.fileno(), select.EPOLLIN)
                            _connections.update({_conn.fileno(): [_conn, _addr]})
                        elif event & select.EPOLLIN: # 文件描述符可读
                            _data = _connections[fileno][0].recv(self._max_data_size)
                            if len(_data) <= 0:
                                _epoll.modify(fileno, select.EPOLLOUT)
                            _epoll.modify(fileno, select.EPOLLOUT)
                            _data = json.loads(_data)

                            for d in _data:
                                self._logQueue.put(d, block = False)
                        elif event & select.EPOLLOUT: # 文件描述符可写
                            _epoll.modify(fileno, 0)
                            _connections[fileno][0].shutdown(socket.SHUT_RDWR)
                        elif event & select.EPOLLHUP: # 文件描述符完成工作
                            # TODO: 出现异常文件描述符没有被关闭
                            _epoll.unregister(fileno)
                            _connections[fileno][0].close()
                            del _connections[fileno]
                except Exception as ex:
                    _f1.write("logsrv error: %s\n" % (ex))
        except Exception as ex:
            _f1.write("logsrv error: %s\n" % (ex))
        finally:
            _epoll.unregister(_server_sock.fileno())
            _epoll.close()
            _server_sock.close()

    def __reload_config(self, signo, frame):
        """
            接收SIGUSR1信号重新加载config.json
        """
        with open(V.config_file) as f:
            config = json.loads(f.read())
            self.applications = config.get(V.applications)

    def __jeter_log(self, signo, frame):
        """
            丢弃日志内容,防止日志内容过多处理不了的情况
        """
        self._logQueue.queue.clear()

    def __get_fd(self, app):
        d = self.__getDay(f = "%Y%m%d")
        fd = self.fds.get(app, {}).get(d, None)
        if fd is not None:
            return fd
        pid = os.getpid()
        filename = "%s-%s-%s.log" % (pid, app, d)
        # 如果logsrv开了多个线程需要使用锁
        # 并且Queue需要使用multiprocessing的Queue
        fd = open(os.path.join(self.path, filename), "a", 1)
        self.fds.update({app: {d: fd}})
        for key in self.fds.get(app).keys():
            if key != d:
                self.fds.get(app).get(key).close()
                del self.fds.get(app)[key]
        return fd

    def __getDay(self, days = 0, f = "%Y-%m-%d"):
        currTime = datetime.datetime.now()
        day = currTime + datetime.timedelta(days)
        return datetime.datetime.strftime(day, f)

    def log(self):
        # [0, 1001, "2017-01-01", "192.168.10.218", "wtf"]
        for x in xrange(1, 10):
            if not self._logQueue.empty():
                data = self._logQueue.get(block = False)
                level = self.lvs[data[0]]
                app_config = self.applications.get(str(data[1]))
                fd = self.__get_fd(app_config.get(V.name))
                if sys.stdout.isatty():
                    print("[%s][%s][%s]: %s" % (level, data[2], data[3], data[4]))
                fd.write("[%s][%s][%s]: %s\n" % (level, data[2], data[3], data[4]))

if __name__ == "__main__":
    pid = os.getpid()
    with open("pid.log", "w") as f:
        f.write(str(pid))
    Server().start()
