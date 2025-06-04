import os
from datetime import datetime
from logging import (
    getLogger,
    StreamHandler,
    FileHandler,
    DEBUG,
    Formatter,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
)
from zoneinfo import ZoneInfo


class JSTFormatter(Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=ZoneInfo("Asia/Tokyo"))
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def get_log_level():
    """環境変数からログレベルを取得"""
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()  # デフォルトをINFOに変更

    level_mapping = {
        "DEBUG": DEBUG,
        "INFO": INFO,
        "WARNING": WARNING,
        "WARN": WARNING,  # WARN も WARNING として扱う
        "ERROR": ERROR,
        "CRITICAL": CRITICAL,
        "FATAL": CRITICAL,  # FATAL も CRITICAL として扱う
    }

    level = level_mapping.get(level_str, INFO)

    # 設定されたログレベルを起動時に表示（デバッグ用）
    if level_str in level_mapping:
        print(f"Log level set to: {level_str}")
    else:
        print(f"Invalid LOG_LEVEL '{level_str}', using INFO as default")

    return level


def setup_logger(name=__name__):
    """JST対応のloggerを設定して返す"""
    logger = getLogger(name)

    # 既にハンドラーが設定されている場合はスキップ
    if logger.handlers:
        return logger

    log_level = get_log_level()

    # StreamHandler
    handler = StreamHandler()
    handler.setLevel(log_level)

    formatter = JSTFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # FileHandler (Docker環境用)
    if os.path.exists("/proc/1/fd/1"):
        handler2 = FileHandler("/proc/1/fd/1")
        handler2.setFormatter(formatter)
        logger.addHandler(handler2)

    logger.setLevel(log_level)
    logger.propagate = False

    return logger
