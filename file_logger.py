# -*- coding: utf-8 -*-


import logging

class FileLogger:
    def __init__(self, appname, filename=None):
        if filename is None:
            self.filename = "{}.log".format(appname)
        self.appname = appname

    def create(self):
        datefmt = "%Y-%m-%d %H:%M:%S"
        fmt = "%(asctime)s %(msecs)s - %(name)s - %(levelname)s %(thread)s %(module)s %(filename)s %(lineno)s %(funcName)s - %(message)s"
        formatter = logging.Formatter(fmt, datefmt=datefmt)

        logger = logging.getLogger(self.appname)
        logger_level = logging.INFO
        logger.setLevel(logger_level)

        # 添加文件处理器
        fh = logging.FileHandler(filename=self.filename, mode="a", encoding="utf8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger
