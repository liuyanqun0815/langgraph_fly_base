import logging

from sale_app.util.traceId_log_handler import TraceIdFilter


class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.hasHandlers():
            # 输出到控制台
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            formatter = logging.Formatter('%(levelname)s %(asctime)s traceId=%(trace_id)s %(message)s')
            console.setFormatter(formatter)
            console.addFilter(TraceIdFilter())
            self.logger.addHandler(console)

            # file_handler = logging.FileHandler(f"{name}.log")
            # formatter = logging.Formatter("%(asctime)s - %(lineno)d -%(levelname)s - %(message)s")
            # file_handler.setFormatter(formatter)
            #
            # self.logger.addHandler(file_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

