"""
日志配置
"""
import os
from loguru import logger
from app.core.config import settings

# 确保日志目录存在
log_dir = os.path.dirname(settings.LOG_FILE)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志
logger.remove()  # 移除默认处理器

# 控制台日志
logger.add(
    sink=lambda msg: print(msg, end=""),
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)

# 文件日志
logger.add(
    settings.LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    encoding="utf-8"
)