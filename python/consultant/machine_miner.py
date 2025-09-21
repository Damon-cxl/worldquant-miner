from time import sleep
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import json
import os
from itertools import product
import requests
import datetime
import sys
# 修复导入语句，确保zdb目录在Python路径中
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入所需模块
import zdb.db_operations
import python.consultant.machine_lib as ml  # 正确导入machine_lib模块并使用ml别名

# 创建log文件夹（如果不存在）
log_dir = os.path.join(project_root, 'log')
os.makedirs(log_dir, exist_ok=True)

# 配置日志，输出到log文件夹下，并确保编码为utf-8
# 检查是否已经配置了日志处理器，避免重复配置
if len(logging.root.handlers) == 0:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            TimedRotatingFileHandler(os.path.join(log_dir, 'machine_mining.txt'), when='midnight', interval=1, backupCount=30, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

# 确保程序退出时正确关闭日志文件
def setup_logging_shutdown_hook():
    import atexit
    import signal
    import threading
    
    # 创建锁以确保线程安全
    log_lock = threading.RLock()
    
    def close_loggers():
        with log_lock:
            # 确保所有日志都被刷新和关闭
            for handler in logging.root.handlers[:]:
                try:
                    handler.flush()
                    handler.close()
                except Exception as e:
                    # 即使出现错误也继续关闭其他处理器
                    print(f"Error closing logger handler: {e}", file=sys.stderr)
    
    # 注册程序退出钩子
    atexit.register(close_loggers)
    
    # 注册信号处理函数
    def signal_handler(sig, frame):
        print(f"收到信号 {sig}，正在优雅关闭...", file=sys.stderr)
        close_loggers()
        sys.exit(0)
    
    # 处理更多类型的信号
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # 终止信号
    
    # 在Windows上可能不支持以下信号，但不会导致错误
    try:
        signal.signal(signal.SIGABRT, signal_handler)  # 异常终止信号
        signal.signal(signal.SIGQUIT, signal_handler)  # 退出信号
    except (AttributeError, ValueError):
        pass

# 设置日志关闭钩子
setup_logging_shutdown_hook()


class MachineMiner:
    def __init__(self, username: str, password: str, level: str):
        self.brain = ml.WorldQuantBrain(username, password, level)
        self.alpha_bag = []
        self.gold_bag = []
        self.database = zdb.db_operations.DataBaseOp()
        
    def mine_alphas(self, region="USA", universe="TOP3000"):
        logging.info(f"Starting machine alpha mining for region: {region}, universe: {universe}")
        
        while True:
            try:
                # Get data fields
                logging.info("Fetching data fields...")
                fields_df = self.brain.get_datafields(region=region, universe=universe)
                logging.info(f"Got {len(fields_df)} data fields")
                
                matrix_fields = self.brain.process_datafields(fields_df, "matrix")
                vector_fields = self.brain.process_datafields(fields_df, "vector")
                logging.info(f"Processed {len(matrix_fields)} matrix fields and {len(vector_fields)} vector fields")
                
                # Generate first order alphas
                logging.info("Generating first order alphas...")
                first_order = self.brain.get_first_order(vector_fields + matrix_fields, self.brain.ops_set, region)
                logging.info(f"Generated {len(first_order)} first order alphas")
                logging.info(f"Sample alphas: {first_order[:3]}")
                
                # Prepare alpha batches
                alpha_list = [(alpha, 0) for alpha in first_order]
                pools = self.brain.load_task_pool(alpha_list, 10, 10)
                logging.info(f"Created {len(pools)} pools with {len(pools[0]) if pools else 0} tasks each")
                
                # Run simulations
                logging.info("Starting simulations...")
                self.brain.multi_simulate(pools, "INDUSTRY", region, universe, 0)
                
                # Process results
                self._process_results()
                
            except Exception as e:
                logging.error(f"Error in mining loop: {str(e)}")
                sleep(600)
                self.brain.login()
                continue

    def _process_results(self):
        # Implementation of _process_results method
        pass

    def save_results(self):
        timestamp = int(time.time())
        results = {
            "timestamp": timestamp,
            "gold_alphas": self.gold_bag
        }
        
        with open(f'machine_results_{timestamp}.json', 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f"Results saved to machine_results_{timestamp}.json")

    def simulate_run(self, dataset_id,dataset_prefix,dataset_dsc,dataset_cat,count=100, offset=0, region='USA',universe='TOP3000',delay=1,neutralize='SUBINDUSTRY',template =False, pool_size=7):
        logging.info(f"开始运行:{dataset_id},{dataset_prefix},{dataset_dsc},{dataset_cat},{count},{offset}, {region},{universe},{delay},{neutralize},{template}, {pool_size}")
        # 获取字段
        pc_fields = self.simulate_fields(region=region,universe=universe,delay=delay, dataset_id=dataset_id,count=count, offset=offset)
        if template:
            # 生成模板表达式-一阶
            first_order = self.first_order_factory_template(pc_fields)
        else:
            # 生成表达式-一阶
            first_order = self.brain.get_first_order(pc_fields, self.brain.ops_set, region)

        #赋予alpha表达式一个初始decay
        init_decay =6
        fo_alpha_list = []
        for alpha in first_order:
            fo_alpha_list.append((alpha, init_decay))

        # 划分任务池  
        fo_pools = self.brain.load_task_pool(fo_alpha_list, 10, pool_size)
        # 一二三阶运行相同的编号
        sim_batch = int(time.time())
        # 一阶运行开始记录
        start_time_one = datetime.datetime.now() - datetime.timedelta(hours=12)
        start_time_one_str = start_time_one.strftime("%Y-%m-%d %H:%M:%S")
        sim_data_one = {"batch_time": sim_batch, "start_time": start_time_one_str, "order_seq": 1, "dataset": dataset_id, "dataset_dsc": dataset_dsc, "dataset_cat": dataset_cat, "region": region, "universe": universe, "delay": delay, "neutralize": neutralize, "field_offset": offset, "field_count": count, "alpha_count": len(first_order), "multi_sum": pool_size, "pool": len(fo_pools), "template": None}

        self.database.save_simulate_record(sim_data_one)
        # 一阶运行
        self.brain.multi_simulate(fo_pools, neutralize, region, universe, 0)
        # 一阶运行结束记录
        end_time_one = datetime.datetime.now() - datetime.timedelta(hours=12)
        end_time_one_str = end_time_one.strftime("%Y-%m-%d %H:%M:%S")
        sim_data_one_update = {"end_time": end_time_one_str}
        self.database.update_simulate_record(sim_data_one_update, sim_batch, 1)
        # 二阶运行
        sec_res = self.simulate_run_second_order(start_time_one_str,end_time_one_str,dataset_prefix,sim_data_one, region,universe,neutralize, pool_size)
        if (sec_res[0]==0):
            return
        # 三阶运行
        self.simulate_run_third_order(sec_res[1],sec_res[2],dataset_prefix,sim_data_one, region,universe,neutralize, pool_size)

    

    def simulate_run_second_order(self, start_time_one_str,end_time_one_str,dataset_prefix,sim_data, region='USA',universe='TOP3000',neutralize='SUBINDUSTRY', pool_size=7):
        # 筛选一阶alpha
        fo_tracker = self.brain.my_get_alphas(start_time_one_str.replace(" ","T"),end_time_one_str.replace(" ","T"), 0.5, 0.4, region, 100,"track", True, "")
        if(len(fo_tracker)==0):
            logging.info("筛选一阶alpha数量：%s"%len(fo_tracker))
            return (len(fo_tracker),"","")
        # 剪枝
        fo_layer=self.brain.prune(fo_tracker,dataset_prefix,5)
        # 生成二阶alpha
        so_alpha_list = []
        group_ops = ["group_neutralize", "group_rank", "group_zscore"]
        for expr, decay in fo_layer:
            for alpha in self.brain.get_group_second_order_factory([expr], group_ops, region):
                so_alpha_list.append((alpha, decay))
        print(len(so_alpha_list))
        so_pools = self.brain.load_task_pool(so_alpha_list, 10, pool_size)
        # 二阶运行开始记录
        start_time = datetime.datetime.now() - datetime.timedelta(hours=12)
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        # 将一阶参数设置成2阶参数
        sim_data["start_time"]=start_time_str
        sim_data["order_seq"]=2
        sim_data["alpha_count"]=len(so_alpha_list)
        sim_data["pool"]=len(so_pools)
        self.database.save_simulate_record(sim_data)
        # 二阶运行
        self.brain.multi_simulate(so_pools, neutralize, region, universe, 0)
        # 二阶运行结束记录
        end_time = datetime.datetime.now() - datetime.timedelta(hours=12)
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        sim_data_update = {"end_time": end_time_str}
        self.database.update_simulate_record(sim_data_update, sim_data["batch_time"], 2)
        return (len(so_alpha_list),start_time_str,end_time_str)

    def simulate_run_third_order(self, start_time_sec_str,end_time_sec_str,dataset_prefix,sim_data, region='USA',universe='TOP3000',neutralize='SUBINDUSTRY', pool_size=7):
        # 筛选2阶alpha
        fo_tracker = self.brain.my_get_alphas(start_time_sec_str.replace(" ","T"),end_time_sec_str.replace(" ","T"), 1.4, 0.7, region, 100,"track", True, "")
        if(len(fo_tracker)==0):
            logging.info("筛选2阶alpha数量：%s"%len(fo_tracker))
            return len(fo_tracker)
        # 剪枝
        fo_layer=self.brain.prune(fo_tracker,dataset_prefix,5)
        # 生成三阶alpha
        th_alpha_list=[]
        for expr,decay in fo_layer:
            for alpha in self.brain.trade_when_factory("trade_when",expr,region):
                th_alpha_list.append((alpha,decay))
        print(len(th_alpha_list))
        so_pools = self.brain.load_task_pool(th_alpha_list, 10, pool_size)
        # 三阶运行开始记录
        start_time = datetime.datetime.now() - datetime.timedelta(hours=12)
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        # 将参数设置成3阶参数
        sim_data["start_time"]=start_time_str
        sim_data["order_seq"]=3
        sim_data["alpha_count"]=len(th_alpha_list)
        self.database.save_simulate_record(sim_data)
        # 3阶运行
        self.brain.multi_simulate(so_pools, neutralize, region, universe, 0)
        # 3阶运行结束记录
        end_time = datetime.datetime.now() - datetime.timedelta(hours=12)
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        sim_data_update = {"end_time": end_time_str}
        self.database.update_simulate_record(sim_data_update, sim_data["batch_time"], 3)
        return len(th_alpha_list)

    def simulate_fields(self, region,universe,delay, dataset_id,count=100, offset=0):
        df = self.brain.get_datafields(region=region, universe=universe, delay=delay, dataset_id=dataset_id, count=count, offset=offset)
        pc_fields = self.brain.process_datafields(df, True)
        return pc_fields

    def first_order_factory_template(fields):
        alpha_set = []
        days = [5,22,60,120,252]
        #for field in fields:
        for field in fields:
        #reverse op does the work
            # alpha_set.append(field)
            #alpha_set.append("-%s"%field)
            ## ts_delta(ts_delta(x,d),d) 加速因子
            for day in days:
                alpha = "(%s - ts_mean(%s, %s)) / ts_mean(%s, %s)"%(field,field, day,field, day)
                alpha_set.append(alpha)
            
        return alpha_set

    def get_datafields_count(self, region,universe,delay, dataset_id):
        return self.brain.get_datafields_count(region=region, delay=delay, universe=universe, dataset_id=dataset_id)
