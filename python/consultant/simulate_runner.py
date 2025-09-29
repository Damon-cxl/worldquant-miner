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
from python.logger_init import get_module_logger

# 创建log文件夹（如果不存在）
log_dir = os.path.join(project_root, 'log')
os.makedirs(log_dir, exist_ok=True)

# 获取模块级别的logger
logger = get_module_logger(__name__, log_dir, 'sim_runner',logging.INFO)

# # 配置日志，输出到log文件夹下，并确保编码为utf-8
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         TimedRotatingFileHandler(os.path.join(log_dir, 'simulate_runner.txt'), when='midnight', interval=1, backupCount=30, encoding='utf-8'),
#         logging.StreamHandler()
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
#             for handler in logging.root.handlers[:]:
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


# 定义全局miner变量，可在整个文件中访问
# 这是使类实例全局可用的一种方式
global_miner = None

def batch_run():
    # 函数通过参数接收miner实例
    # region='USA'
    # universe='TOP3000'
    # region='GLB'
    # universe='TOPDIV3000'
    universe='MINVOL1M'
    region='ASI'
    # universe='ILLIQUID_MINVOL1M'
    delay=1
    neutralize='SUBINDUSTRY'
    # neutralize='SLOW_AND_FAST'
    # neutralize='FAST'
    # template =True
    template =False
    pool_size=7
    dataset_id="analyst15"
    dataset_prefix="anl15"
    dataset_dsc="Earnings forecasts"
    # dataset_cat="Risk"
    # dataset_cat="Fundamental"
    dataset_cat="Analyst"
    # 过滤出coverage覆盖率大于0.7的字段
    other_para = "&coverage%3E=0.7"
    field_count = global_miner.get_datafields_count(region=region, delay=delay, universe=universe, dataset_id=dataset_id,other_para=other_para)
    # field_count = 1
    count = 0
    offset = 0
    step = 2
    if field_count < step:
        step = field_count
    for i in range(offset, field_count, step):
        count = count + step
        global_miner.simulate_run(dataset_id,dataset_prefix,dataset_dsc,dataset_cat,count, offset, region,universe,delay,neutralize,template, pool_size)
        offset = offset + step

def batch_run_next():
    batch_time = [1758511676,1758534787,1758529659,1758585792]
    for t in batch_time:
        global_miner.simulate_run_next(t)
# 在main函数中初始化并使用

def main():
    global global_miner  # 声明使用全局变量
    
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
    global_miner = machine_miner.MachineMiner(username, password, level, logger)
    batch_run()
    # batch_run_next()

if __name__ == "__main__":
    main()