# -*- coding: utf-8 -*-
"""
日志配置模块
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import colorlog


class LoggerSetup:
    """日志设置类"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def setup_logger(
        self,
        name: str,
        level: str = "INFO",
        console_output: bool = True,
        file_output: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """设置并返回配置好的logger"""

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))

        # 清除现有的处理器
        logger.handlers.clear()

        # 创建格式化器
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台输出（带颜色）
        if console_output:
            console_handler = colorlog.StreamHandler(sys.stdout)
            console_formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # 文件输出
        if file_output:
            # 按日期创建日志文件
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"{name}_{today}.log"

            # 使用RotatingFileHandler进行日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)

            # 错误日志单独记录
            error_log_file = self.log_dir / f"{name}_error_{today}.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            logger.addHandler(error_handler)

        return logger


# 全局日志设置实例
logger_setup = LoggerSetup()

# 创建各个模块的logger
api_logger = logger_setup.setup_logger("api", level="INFO")
llm_logger = logger_setup.setup_logger("llm_service", level="INFO")
transcript_logger = logger_setup.setup_logger("transcript_service", level="INFO")
app_logger = logger_setup.setup_logger("app", level="INFO")


def log_function_call(logger: logging.Logger):
    """装饰器：记录函数调用"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"调用函数 {func.__name__}，参数: args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator


def log_api_request(logger: logging.Logger):
    """装饰器：记录API请求"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 提取请求信息
            request_info = {}
            for arg in args:
                if hasattr(arg, 'method'):  # FastAPI Request对象
                    request_info = {
                        'method': arg.method,
                        'url': str(arg.url),
                        'headers': dict(arg.headers),
                        'client': arg.client.host if arg.client else None
                    }
                    break

            logger.info(f"API请求开始: {func.__name__}, 请求信息: {request_info}")

            try:
                result = await func(*args, **kwargs)
                logger.info(f"API请求成功: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"API请求失败: {func.__name__}, 错误: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator