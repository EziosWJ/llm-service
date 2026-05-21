# 日志配置：统一设置根 logger 的级别和输出格式

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """配置根 logger：设置级别、输出到 stdout、统一时间格式"""
    logger = logging.getLogger()
    logger.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # 防止 uvicorn reload 时重复添加 handler
    if not logger.handlers:
        logger.addHandler(handler)
