import logging


class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        # 输出到控制台
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        # logging.getLogger('').addHandler(console)
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

