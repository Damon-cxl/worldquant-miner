import logging
import os
from logging.handlers import TimedRotatingFileHandler
import time

# 1. 获取Logger实例 - 推荐使用模块名作为Logger名称
def get_module_logger(module_name, log_dir, log_name=None, log_level=logging.INFO):
    print("module_name: ", module_name)
    # 创建Logger实例
    logger = logging.getLogger(module_name)
    
    # 设置Logger级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    logger.setLevel(log_level)
    
    # 检查是否已经添加了处理器（避免重复添加）
    if not logger.handlers:
        # 2. 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)  # 控制台只输出INFO及以上级别
        
        # 3. 创建文件处理器 - 使用TimedRotatingFileHandler实现日志轮转
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        if log_name is None:
            log_name = "ALL"
        else:
            log_name = log_name + ".txt"
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, log_name),
            when="midnight",  # 在午夜时分轮转
            interval=1,       # 每天轮转一次
            backupCount=30,   # 保留30个备份文件
            encoding="utf-8"  # 确保中文正常显示
        )
        file_handler.setLevel(log_level)  # 文件记录INFO及以上所有级别
        
        # 4. 创建格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # 为处理器设置格式化器
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # 5. 将处理器添加到Logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger