"""
统一日志配置模块

集中管理日志设置，使用 RotatingFileHandler 限制日志文件大小。
替代 launcher.py 和 main.py 中各自调用 logging.basicConfig() 的方式。
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from core.paths import LOGS_DIR, ensure_directories


def setup_logging(log_name="lovelymem", level=logging.INFO):
    """
    配置统一的日志系统。
    
    Args:
        log_name: 日志文件名前缀
        level: 日志级别
    
    Returns:
        配置好的 root logger
    """
    ensure_directories()
    
    log_file = LOGS_DIR / f"{log_name}.log"
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器 - 带旋转，最大 5MB，保留 3 个备份
    file_handler = RotatingFileHandler(
        str(log_file),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # 配置 root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除已有的 handlers 避免重复
    root_logger.handlers.clear()
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger
