import sys
import os
from loguru import logger


def setup_logger():
    # 移除所有默认的 handler，防止重复或错误
    logger.remove()

    # 1. 尝试输出到控制台 (仅在开发环境或有控制台时有效)
    if sys.stderr:
        try:
            logger.add(
                sys.stderr,
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
            )
        except Exception:
            # 如果 sys.stderr 存在但无法写入（某些打包环境），静默失败，不崩溃
            pass

    # 2. 输出到文件 (这是打包后的主要调试手段)
    # 获取日志文件的存储路径 (兼容打包环境)
    if getattr(sys, 'frozen', False):
        # 打包后，日志存在可执行文件同级目录下
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    log_path = os.path.join(base_dir, "app.log")

    # 添加文件 Logger
    logger.add(
        log_path,
        rotation="5 MB",
        retention="10 days",
        level="INFO",
        encoding="utf-8"
    )