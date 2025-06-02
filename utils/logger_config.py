import os
from logging import getLogger, StreamHandler, FileHandler, DEBUG, Formatter
from datetime import datetime
from zoneinfo import ZoneInfo


class JSTFormatter(Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=ZoneInfo("Asia/Tokyo"))
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def setup_logger(name=__name__):
    """JST対応のloggerを設定して返す"""
    logger = getLogger(name)

    # 既にハンドラーが設定されている場合はスキップ
    if logger.handlers:
        return logger

    # StreamHandler
    handler = StreamHandler()
    handler.setLevel(DEBUG)

    formatter = JSTFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # FileHandler (Docker環境用)
    if os.path.exists("/proc/1/fd/1"):
        handler2 = FileHandler("/proc/1/fd/1")
        handler2.setFormatter(formatter)
        logger.addHandler(handler2)

    logger.setLevel(DEBUG)
    logger.propagate = False

    return logger
