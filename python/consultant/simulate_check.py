from time import sleep
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import json
import os
import requests
import datetime
import sys
# 修复导入语句，确保zdb目录在Python路径中
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入machine_miner模块
from python.consultant import machine_miner
import python.consultant.machine_lib as ml
from python.logger_init import get_module_logger

# 创建log文件夹（如果不存在）
log_dir = os.path.join(project_root, 'log')
os.makedirs(log_dir, exist_ok=True)

# 获取模块级别的logger
logger = get_module_logger(__name__, log_dir, 'sim_check',logging.INFO)

# # 配置日志，输出到log文件夹下，并确保编码为utf-8
# logger.basicConfig(
#     level=logger.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         TimedRotatingFileHandler(os.path.join(log_dir, 'simulate_check.txt'), when='midnight', interval=1, backupCount=30, encoding='utf-8'),
#         logger.StreamHandler()
#     ]
# )

# # 确保程序退出时正确关闭日志文件
# def setup_logging_shutdown_hook():
#     import atexit
#     import signal
#     import threading
    
#     # 创建锁以确保线程安全
#     log_lock = threading.RLock()
    
#     def close_loggers():
#         with log_lock:
#             # 确保所有日志都被刷新和关闭
#             for handler in logger.root.handlers[:]:
#                 try:
#                     handler.flush()
#                     handler.close()
#                 except Exception as e:
#                     # 即使出现错误也继续关闭其他处理器
#                     print(f"Error closing logger handler: {e}", file=sys.stderr)
    
#     # 注册程序退出钩子
#     atexit.register(close_loggers)
    
#     # 注册信号处理函数
#     def signal_handler(sig, frame):
#         print(f"收到信号 {sig}，正在优雅关闭...", file=sys.stderr)
#         close_loggers()
#         sys.exit(0)
    
#     # 处理更多类型的信号
#     signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
#     signal.signal(signal.SIGTERM, signal_handler) # 终止信号
    
#     # 在Windows上可能不支持以下信号，但不会导致错误
#     try:
#         signal.signal(signal.SIGABRT, signal_handler)  # 异常终止信号
#         signal.signal(signal.SIGQUIT, signal_handler)  # 退出信号
#     except (AttributeError, ValueError):
#         pass

# # 设置日志关闭钩子
# setup_logging_shutdown_hook()

class CheckSubmission:
    def __init__(self, username: str, password: str, level: str, logger: logging.Logger = None):
        self.brain = ml.WorldQuantBrain(username, password, level, logger)
        self.alpha_bag = []
        self.gold_bag = []
        self.logger = logger
        # self.region_list = ["USA", "GLB", "ASI"]
        self.region_list = ["GLB", "ASI"]
        self.tags = ["SharpFit2","Sharp2","MayPPA"]

    def check_alpha(self):
        start_time = "2025-09-16T00:00:00"
        end_time = "2025-09-17T00:00:00"
        other_para = "&is.returns%3E=0.1&is.turnover%3C0.4&is.margin%3E=0.0005"
        for region in self.region_list:
            for tag in self.tags:
                if tag == "SharpFit2":
                    sharp = 2
                    fit = 2
                elif tag == "Sharp2":
                    sharp = 2
                    fit = 1
                    other_para += "&is.fitness%3C2"
                elif tag == "MayPPA":
                    sharp = 1.1
                    fit = 0
                    other_para += "&is.sharpe%3C2&is.fitness%3C1"
                self.check_alpha_region(region, start_time, end_time, sharp, fit, tag, other_para)
        

    def check_alpha_region(self, region: str, start_time: str, end_time: str, sharp: float, fit: float, tag: str, other_para: str):
        th_tracker=self.brain.my_get_alphas(start_time, end_time, sharp, fit, region, 200,"submit", True, other_para)
        self.logger.info(f"check_alpha_region_get: {tag} {region} {len(th_tracker)}")
        if th_tracker is None or len(th_tracker) == 0:
            return
        #将get的alpha的id取出至stone_bag,用apicheck submission
        stone_bag = []
        check_bag = []
        for alpha in th_tracker:
            if len(alpha['tags']) > 0:
                continue
            stone_bag.append(alpha['id'])
        self.logger.info(f"check_alpha_region_get_filt_tag: {tag} {region} {len(stone_bag)}")
        if len(stone_bag) == 0:
            return
        self.brain.check_submission(stone_bag, check_bag, 0, tags=[tag])
        self.logger.info(f"check_submission: {tag} {region} {len(stone_bag)} {len(check_bag)}")
        # self.logger.info(f"check_submission: {check_bag}")
        


# 在main函数中初始化并使用

def main():
    # Read credentials from credential.txt
    try:
        with open(project_root + '/credential.txt', 'r') as f:
            credentials = json.load(f)
        username = credentials[0]
        password = credentials[1]
        level = credentials[2]
    except (FileNotFoundError, json.JSONDecodeError, IndexError) as e:
        raise ValueError(f"Error reading credentials from credential.txt: {e}")
    
    if not username or not password:
        raise ValueError("Invalid credentials in credential.txt")
        
    # 方法1: 创建实例并作为参数传递（当前实现）
    # miner = machine_miner.MachineMiner(username, password, level)
    # batch_run(miner)
    
    # 方法2: 创建实例并赋值给全局变量（可选实现）
    check = CheckSubmission(username, password, level, logger)
    check.check_alpha()

if __name__ == "__main__":
    main()