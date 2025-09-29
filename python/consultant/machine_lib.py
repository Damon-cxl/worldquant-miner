import requests
from os import environ
from time import sleep
import time
import json
import pandas as pd
import random
import pickle
from itertools import product
from itertools import combinations
from collections import defaultdict
import pickle
import logging
import threading
from requests import Response
import concurrent
import concurrent.futures
from tqdm import tqdm

arsenal_E = ["ts_moment", "ts_entropy", "ts_min_max_cps", "ts_min_max_diff", "inst_tvr", 'sigmoid', 
           "ts_decay_exp_window", "ts_percentage", "vector_neut", "vector_proj", "signed_power"]

arsenal_G = ["inst_tvr", 
           "ts_decay_exp_window", "vector_neut", "signed_power"]

group_ops_E = ["group_rank", "group_sum", "group_max", "group_mean", "group_median", "group_min", "group_std_dev"]
group_ops_G = ["group_rank",  "group_mean", "group_median"]

twin_field_ops = ["ts_corr", "ts_covariance", "ts_co_kurtosis", "ts_co_skewness", "ts_theilsen"]
class WorldQuantBrain:
    def __init__(self, username: str, password: str, level: str, logger: logging.Logger = None):
        self.username = username
        self.password = password
        self.level = level
        self.session = None
        self.logger = logger
        self.desc =  "Idea: \nThis alpha identifies stocks with extreme negative debt service ratio trends, neutralized by relation-based cluster effects. It targets stocks with the most extreme negative 180-day quantile rankings within their relation-based clusters. The strategy is based on the premise that stocks with extreme negative debt service characteristics, when adjusted for relation-based cluster factors, may indicate potential mispricing.\nRationale for data used: \noth450_mfm_gem3_dsrt\nThis debt service ratio data field measures a company's ability to service its debt obligations. Low values suggest difficulty in meeting debt obligations, while high values indicate strong capacity to service debt. By focusing on this metric, this alpha targets stocks with extreme debt service characteristics.\nRationale for operators used: \nts_quantile(..., 180)\nCalculates the quantile ranking of debt service ratio values over a 180-day window, capturing long-term debt service ratio patterns. This operator transforms absolute values into relative rankings from 0 to 1, enabling comparison across stocks with different scales."
        self.basic_ops_E = ["log", "sqrt", "reverse", "inverse", "rank", "zscore", "log_diff", "s_log_1p",
                         'fraction', 'quantile', "normalize", "scale_down"]
        self.basic_ops_G = ["log", "sqrt", "reverse", "inverse", "rank", "zscore", "s_log_1p",
                         'quantile', "normalize", ]
        self.ts_ops_E = ["ts_rank", "ts_zscore", "ts_delta", "ts_sum", "ts_product", "ts_delay",
                      "ts_ir", "ts_std_dev", "ts_mean", "ts_arg_min", "ts_arg_max", "ts_min_diff",
                      "ts_max_diff", "ts_returns", "ts_scale", "ts_skewness", "ts_kurtosis",  
                      "ts_quantile"]
        self.ts_ops_G = ["ts_rank", "ts_zscore", "ts_delta", "ts_sum", "ts_product", "ts_delay",
                       "ts_std_dev", "ts_mean", "ts_arg_min", "ts_arg_max", 
                        "ts_scale",  
                      "ts_quantile"]
        if self.level == "G":
            self.ops_set = self.basic_ops_G + self.ts_ops_G + arsenal_G + group_ops_G
        elif self.level == "E":
            self.ops_set = self.basic_ops_E + self.ts_ops_E + arsenal_E + group_ops_E
        elif self.level == "M":
            self.ops_set = self.basic_ops_E + self.ts_ops_E + arsenal_E + group_ops_E
        elif self.level == "GM":
            self.ops_set = self.basic_ops_E + self.ts_ops_E + arsenal_E + group_ops_E
        self.login()

    def login(self):
        """Initialize or refresh session with WorldQuant Brain."""
        self.logger.info("Authenticating with WorldQuant Brain...")
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        response = self.session.post('https://api.worldquantbrain.com/authentication')
        
        if response.status_code != 201:
            raise Exception(f"Authentication failed: {response.text}")
            
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.logger.info("Authentication successful")
        return self.session

    def multi_simulate(self, alpha_pools: list, neut: str, region: str, universe: str, start: int = 0):
        """Run multiple alpha simulations in parallel."""
        self.logger.info(f"Starting multi-simulate for {len(alpha_pools)} pools")
        
        for x, pool in enumerate(alpha_pools):
            if x < start:
                continue
                
            progress_urls = []
            self.logger.info(f"Processing pool {x+1}/{len(alpha_pools)}")
            
            for y, task in enumerate(pool):
                sim_data_list = self.generate_sim_data(task, region, universe, neut)
                self.logger.info(f"Generated simulation data for task {y+1}/{len(pool)}")
                # self.logger.info(f"Simulation data: {sim_data_list}")
                try:
                    simulation_response = self.session.post('https://api.worldquantbrain.com/simulations', 
                                                         json=sim_data_list)
                    if simulation_response.status_code == 401:
                        self.logger.info("Session expired, re-authenticating...")
                        self.login()
                        simulation_response = self.session.post('https://api.worldquantbrain.com/simulations', 
                                                            json=sim_data_list)
                    
                    if simulation_response.status_code != 201:
                        self.logger.error(f"Simulation API error: {simulation_response.text}")
                        self.logger.error(f"Simulation API error alphas: {task}")
                        continue
                        
                    simulation_progress_url = simulation_response.headers.get('Location')
                    if not simulation_progress_url:
                        self.logger.error("No Location header in response")
                        continue
                        
                    progress_urls.append(simulation_progress_url)
                    self.logger.info(f"Posted simulation for task {y+1}, got progress URL: {simulation_progress_url}")
                    
                except Exception as e:
                    self.logger.error(f"Error posting simulation: {str(e)}")
                    sleep(600)
                    self.login()
                    continue

            self._monitor_progress(progress_urls)
            self.logger.info(f"Pool {x+1} simulations completed")

    def _monitor_progress(self, progress_urls: list):
        """Monitor simulation progress."""
        for j, progress in enumerate(progress_urls):
            try:
                while True:
                    simulation_progress = self.session.get(progress)
                    retry_after = simulation_progress.headers.get("Retry-After", 0)
                    if not retry_after:
                        break
                    sleep(float(retry_after))

                status = simulation_progress.json().get("status")
                self.logger.info(f"Task {j+1} status: {status}")
                if status != "COMPLETE":
                    self.logger.warning(f"Task not complete: {progress}")

            except Exception as e:
                self.logger.error(f"Error monitoring progress: {str(e)}")

    def generate_sim_data(self, alpha_list, region, uni, neut):
        sim_data_list = []
        maxTrade = 'OFF'
        if region == 'ASI':
            maxTrade = 'ON'
        for alpha, decay in alpha_list:
            simulation_data = {
                'type': 'REGULAR',
                'settings': {
                    'instrumentType': 'EQUITY',
                    'region': region,
                    'universe': uni,
                    'delay': 1,
                    'decay': decay,
                    'neutralization': neut,
                    'truncation': 0.08,
                    'pasteurization': 'ON',
                    'unitHandling': 'VERIFY',
                    'nanHandling': 'OFF',
                    'language': 'FASTEXPR',
                    'visualization': False,
                    'maxTrade': maxTrade,
                },
                'regular': alpha}

            sim_data_list.append(simulation_data)
        return sim_data_list

    def locate_alpha(self, alpha_id):
        alpha = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id)
        string = alpha.content.decode('utf-8')
        metrics = json.loads(string)
        #print(metrics["regular"]["code"])
        
        dateCreated = metrics["dateCreated"]
        sharpe = metrics["is"]["sharpe"]
        fitness = metrics["is"]["fitness"]
        turnover = metrics["is"]["turnover"]
        margin = metrics["is"]["margin"]
        decay = metrics["settings"]["decay"]
        exp = metrics['regular']['code']
        
        triple = [sharpe, fitness, turnover, margin, dateCreated, alpha_id, exp, decay]
    
        return triple

    def set_alpha_properties(self,
        alpha_id,
        name: str = None,
        color: str = None,
        selection_desc: str = None,
        combo_desc: str = None,
        tags: str = ["ace_tag"],
        regular_desc: str = None,
    ):
        """
        Function changes alpha's description parameters
        """
    
        params = {
            "color": color,
            "name": name,
            "tags": tags,
            "category": None,
            "regular": {"description": regular_desc},
            # "combo": {"description": combo_desc},
            # "selection": {"description": selection_desc},
        }
        try:
            response = self.session.patch(
                "https://api.worldquantbrain.com/alphas/" + alpha_id, json=params
            )
            # print(alpha_id)
            # print(response.json())
        except Exception as e:
            self.logger.error(f"set_alpha_properties {alpha_id} error: {str(e)}")
            return
    
    def check_submission(self, alpha_bag, gold_bag, start, tags: list = None):
        depot = []
        for idx, g in enumerate(alpha_bag):
            if idx < start:
                continue
            if idx % 5 == 0:
                print(idx)
            if idx % 200 == 0:
                self.login()
            #print(idx)
            pc = self.get_check_submission(g)
            if pc == "sleep":
                sleep(100)
                self.login()
                alpha_bag.append(g)
            elif pc != pc:
                # pc is nan
                print("check self-corrlation error")
                sleep(100)
                alpha_bag.append(g)
            elif pc == "fail":
                continue
            elif pc == "error":
                depot.append(g)
            else:
                gold_bag.append((g, pc))
                # 设置alpha的属性
                self.set_alpha_properties(g, name=None, tags=tags, regular_desc=self.desc)
                self.logger.info(f"check_pass: {g} {pc}")
        self.logger.info(f"check_submission depot: {depot}")
        return gold_bag

    def get_check_submission(self, alpha_id):
        while True:
            # 设置alpha的属性
            self.set_alpha_properties(alpha_id, name=None, tags=["Checking"], regular_desc=self.desc)
            # Check
            result = self.session.get("https://api.worldquantbrain.com/alphas/" + alpha_id + "/check")
            if "retry-after" in result.headers:
                time.sleep(float(result.headers["Retry-After"]))
            else:
                break
        try:
            if result.json().get("is", 0) == 0:
                print("logged out")
                return "sleep"
            checks_df = pd.DataFrame(
                    result.json()["is"]["checks"]
            )
            pc = checks_df[checks_df.name == "PROD_CORRELATION"]["value"].values[0]
            if not any(checks_df["result"] == "FAIL"):
                return pc
            else:
                return "fail"
        except:
            print("catch: %s"%(alpha_id))
            return "error"
            
    def get_vec_fields(self, fields):
        if self.level == 'G':
            vec_ops = ["vec_avg", "vec_sum", "vec_count"]
        elif self.level == 'E':
            vec_ops = ["vec_avg", "vec_sum", "vec_ir", "vec_max", "vec_count","vec_skewness","vec_stddev", "vec_choose"]
        elif self.level == 'M':
            vec_ops = ["vec_avg", "vec_sum", "vec_ir", "vec_max", "vec_count","vec_skewness","vec_stddev", "vec_choose"]
        elif self.level == 'GM':
            vec_ops = ["vec_avg", "vec_sum", "vec_ir", "vec_max", "vec_count","vec_skewness","vec_stddev", "vec_choose"]
        vec_fields = []
     
        for field in fields:
            for vec_op in vec_ops:
                if vec_op == "vec_choose":
                    vec_fields.append("%s(%s, nth=-1)"%(vec_op, field))
                    vec_fields.append("%s(%s, nth=0)"%(vec_op, field))
                else:
                    vec_fields.append("%s(%s)"%(vec_op, field))
     
        return(vec_fields)

    def get_datafields(self,
        instrument_type: str = 'EQUITY',
        region: str = 'USA',
        delay: int = 1,
        universe: str = 'TOP3000',
        dataset_id: str = '',
        search: str = '',
        count: int = 100,
        offset: int = 0,
        other_para: str = "",
    ):
        step = 50
        if(count - offset<step):
            step = count - offset
        if len(search) == 0:
            url_template = (
                "https://api.worldquantbrain.com/data-fields?"
                + f"instrumentType={instrument_type}"
                + f"&region={region}&delay={str(delay)}&universe={universe}&dataset.id={dataset_id}&limit={step}"
                + f"{other_para}"
                + "&offset={x}"
            )
        else:
            url_template = (
                "https://api.worldquantbrain.com/data-fields?"
                + f"instrumentType={instrument_type}"
                + f"&region={region}&delay={str(delay)}&universe={universe}&limit={step}"
                + f"&search={search}"
                + f"{other_para}"
                + "&offset={x}"
            )
        
        datafields_list = []
        for x in range(offset, count, step):
            datafields = self.session.get(url_template.format(x=x))
            datafields_list.append(datafields.json()['results'])
     
        datafields_list_flat = [item for sublist in datafields_list for item in sublist]
     
        datafields_df = pd.DataFrame(datafields_list_flat)
        return datafields_df
    
    def get_datafields_count(
        self,
        instrument_type: str = "EQUITY",
        region: str = "USA",
        delay: int = 1,
        universe: str = "TOP3000",
        dataset_id: str = "",
        search: str = "",
        other_para: str = "",
    ):
        if len(search) == 0:
            url_template = (
                "https://api.worldquantbrain.com/data-fields?"
                + f"instrumentType={instrument_type}"
                + f"&region={region}&delay={str(delay)}&universe={universe}&dataset.id={dataset_id}&limit=1"
                + f"{other_para}"
                + "&offset=0"
            )
        else:
            url_template = (
                "https://api.worldquantbrain.com/data-fields?"
                + f"instrumentType={instrument_type}"
                + f"&region={region}&delay={str(delay)}&universe={universe}&limit=1"
                + f"&search={search}"
                + f"{other_para}"
                + "&offset=0"
            )
            
        datafields = self.session.get(url_template)
        return datafields.json()["count"]

    def process_datafields(self, df, backfill: bool = False):
        datafields = []
        datafields += df[df['type'] == "MATRIX"]["id"].tolist()
        datafields += self.get_vec_fields(df[df['type'] == "VECTOR"]["id"].tolist())
        if backfill:
            # return ["winsorize(ts_backfill(%s,120),std=4)" % field for field in datafields]
            tb_fields = []
            for field in datafields:
                tb_fields.append("winsorize(ts_backfill(%s, 120), std=4)"%field)
                tb_fields.append(field)
            return tb_fields
        else:
            return datafields
        
     
    def view_alphas(self, gold_bag):
        sharp_list = []
        for gold, pc in gold_bag:

            triple = self.locate_alpha(gold)
            # triple = [sharpe, fitness, turnover, margin, dateCreated, alpha_id, exp, decay]
            info = [triple[0], triple[1], triple[2], triple[3], triple[4], triple[5], triple[6]]
            info.append(pc)
            sharp_list.append(info)

        sharp_list.sort(reverse=True, key = lambda x : x[0])
        for i in sharp_list:
            print(i)
     
    def get_alphas(self, start_date, end_date, sharpe_th, fitness_th, region, alpha_num, usage):
        next_alphas = []
        decay_alphas = []
        # 3E large 3C less
        count = 0
        for i in range(0, alpha_num, 100):
            print(i)
            url_e = "https://api.worldquantbrain.com/users/self/alphas?limit=100&offset=%d"%(i) \
                    + "&status=UNSUBMITTED%1FIS_FAIL&dateCreated%3E=2025-" + start_date  \
                    + "T00:00:00-04:00&dateCreated%3C2025-" + end_date \
                    + "T00:00:00-04:00&is.fitness%3E" + str(fitness_th) + "&is.sharpe%3E" \
                    + str(sharpe_th) + "&settings.region=" + region + "&order=-is.sharpe&hidden=false&type!=SUPER"
            url_c = "https://api.worldquantbrain.com/users/self/alphas?limit=100&offset=%d"%(i) \
                    + "&status=UNSUBMITTED%1FIS_FAIL&dateCreated%3E=2025-" + start_date  \
                    + "T00:00:00-04:00&dateCreated%3C2025-" + end_date \
                    + "T00:00:00-04:00&is.fitness%3C-" + str(fitness_th) + "&is.sharpe%3C-" \
                    + str(sharpe_th) + "&settings.region=" + region + "&order=is.sharpe&hidden=false&type!=SUPER"
            urls = [url_e]
            if usage != "submit":
                urls.append(url_c)
            for url in urls:
                response = self.session.get(url)
                #print(response.json())
                try:
                    alpha_list = response.json()["results"]
                    #print(response.json())
                    for j in range(len(alpha_list)):
                        alpha_id = alpha_list[j]["id"]
                        name = alpha_list[j]["name"]
                        dateCreated = alpha_list[j]["dateCreated"]
                        sharpe = alpha_list[j]["is"]["sharpe"]
                        fitness = alpha_list[j]["is"]["fitness"]
                        turnover = alpha_list[j]["is"]["turnover"]
                        margin = alpha_list[j]["is"]["margin"]
                        longCount = alpha_list[j]["is"]["longCount"]
                        shortCount = alpha_list[j]["is"]["shortCount"]
                        decay = alpha_list[j]["settings"]["decay"]
                        exp = alpha_list[j]['regular']['code']
                        count += 1
                        #if (sharpe > 1.2 and sharpe < 1.6) or (sharpe < -1.2 and sharpe > -1.6):
                        if (longCount + shortCount) > 100:
                            if sharpe < -1.2:
                                exp = "-%s"%exp
                            rec = [alpha_id, exp, sharpe, turnover, fitness, margin, dateCreated, decay]
                            print(rec)
                            if turnover > 0.7:
                                rec.append(decay*4)
                                decay_alphas.append(rec)
                            elif turnover > 0.6:
                                rec.append(decay*3+3)
                                decay_alphas.append(rec)
                            elif turnover > 0.5:
                                rec.append(decay*3)
                                decay_alphas.append(rec)
                            elif turnover > 0.4:
                                rec.append(decay*2)
                                decay_alphas.append(rec)
                            elif turnover > 0.35:
                                rec.append(decay+4)
                                decay_alphas.append(rec)
                            elif turnover > 0.3:
                                rec.append(decay+2)
                                decay_alphas.append(rec)
                            else:
                                next_alphas.append(rec)
                except:
                    print("%d finished re-login"%i)
                    self.login()

        output_dict = {"next" : next_alphas, "decay" : decay_alphas}
        print("count: %d"%count)
        return output_dict
    
    ## filter_flag：控制是否执行厂字alpha筛除
    ## other_params: 拼接的查询参数，如 '&pnl>10000000'
    def my_get_alphas(self, start_date, end_date, sharpe_th, fitness_th, region, alpha_num, usage, filter_flag, other_params = '', filter_tags = True):
        
        next_alphas = []
        decay_alphas = []
        result_list = []
        # 3E large 3C less
        count = 0
        
        url_e = ("https://api.worldquantbrain.com/users/self/alphas?"
                    +"limit={limit}"
                    + "&offset={x}"
                    + f"&status=UNSUBMITTED%1FIS_FAIL&dateCreated%3E={start_date}"
                    + f"-04:00&dateCreated%3C{end_date}"
                    + f"-04:00&is.fitness%3E={str(fitness_th)}&is.sharpe%3E={str(sharpe_th) }"
                    + f"&settings.region={region}&order=-is.sharpe&hidden=false&type!=SUPER{other_params}")
        url_c = ("https://api.worldquantbrain.com/users/self/alphas?"
                    +"limit={limit}"
                    + "&offset={x}"
                    + f"&status=UNSUBMITTED%1FIS_FAIL&dateCreated%3E={start_date}"
                    + f"-04:00&dateCreated%3C{end_date}"
                    + f"-04:00&is.fitness%3C=-{str(fitness_th)}&is.sharpe%3C=-{str(sharpe_th) }"
                    + f"&settings.region={region}&order=is.sharpe&hidden=false&type!=SUPER{other_params}")
        urls = [url_e]
        if usage != "submit":
            urls.append(url_c)
        for url in urls:
            if usage == "submit":
                # 提交Check时，获取总数循环处理
                count_response = self.session.get(url.format(x=0, limit=1))
                alpha_num = count_response.json()["count"]
                if alpha_num == 0:
                    continue
            step = 100
            if alpha_num < step:
                step = alpha_num
            for i in range(0, alpha_num, step):
                response = self.session.get(url.format(x=i, limit=step))
                # print(url)
                # print(response.json())
                try:
                    alpha_list = response.json()["results"]
                    #print(response.json())
                    if(len(alpha_list) <= 0):
                        break
                    for j in range(len(alpha_list)):
                        if usage == "submit" and filter_tags:
                            if len(alpha_list[j]['tags']) > 0:
                                continue
                        alpha_id = alpha_list[j]["id"]
                        name = alpha_list[j]["name"]
                        tags = alpha_list[j]['tags']
                        dateCreated = alpha_list[j]["dateCreated"]
                        sharpe = alpha_list[j]["is"]["sharpe"]
                        fitness = alpha_list[j]["is"]["fitness"]
                        turnover = alpha_list[j]["is"]["turnover"]
                        margin = alpha_list[j]["is"]["margin"]
                        longCount = alpha_list[j]["is"]["longCount"]
                        shortCount = alpha_list[j]["is"]["shortCount"]
                        decay = alpha_list[j]["settings"]["decay"]
                        exp = alpha_list[j]['regular']['code']
                        count += 1

                        if usage != "submit":
                            if (longCount + shortCount) > 100:
                                if sharpe < -sharpe_th:
                                    exp = "-%s"%exp
                                if turnover > 0.7:
                                    decay=decay*4
                                elif turnover > 0.6:
                                    decay=decay*3+3
                                elif turnover > 0.5:
                                    decay=decay*3
                                elif turnover > 0.4:
                                    decay=decay*2
                                elif turnover > 0.35:
                                    decay=decay+4
                                elif turnover > 0.3:
                                    decay=decay+2
                                alpha_data = {'id': alpha_id, 'sharpe':sharpe, 'fitness':fitness, 'turnover': turnover, 'margin':margin,'longCount':longCount,'shortCount':shortCount,'dateCreate':dateCreated,'exp':exp,'decay':decay,'tags':tags}
                                result_list.append(alpha_data)
                        else:
                            checks = alpha_list[j]["is"]["checks"]
                            pass_flag = True
                            for check in checks:
                                if check["result"] == "FAIL":
                                    pass_flag = False
                            if pass_flag:
                                alpha_data = {'id': alpha_id, 'sharpe':sharpe, 'fitness':fitness, 'turnover': turnover, 'margin':margin,'longCount':longCount,'shortCount':shortCount,'dateCreate':dateCreated,'exp':exp,'decay':decay,'tags':tags}
                                result_list.append(alpha_data)
                                # print(alpha_data)
                except Exception as e:
                    print(f"{i} finished re-login: {str(e)}")
                    self.login()

        final_result = []
        if filter_flag:
            print('######### 筛除厂子形alpha #########')
            removed_alpha_ids = []
            lock = threading.Lock()  # 线程锁，防止数据竞争

            if len(result_list) > 1000:
                print('    alpha数量超1000，避免限流，未执行筛除...')
            else:
                total_alphas = len(result_list)
                print(f'    alpha数量 {total_alphas}，开始执行筛除（多线程）...')

                def process_alpha(rec):
                    zero_year_sharp = 0
                    try:
                        response = self.wait_get(f'https://api.worldquantbrain.com/alphas/{rec["id"]}/recordsets/yearly-stats')
                        if response.status_code == 200:
                            yearly_status = response.json()['records']
                            for year_data in yearly_status:
                                if year_data[6] == 0:
                                    zero_year_sharp += 1
                        else:
                            print(f"    获取alpha {rec['id']} 年度统计信息失败，状态码: {response.status_code}")
                    except Exception as e:
                        print(f"    处理alpha {rec['id']} 时发生异常: {str(e)}")
                    
                    with lock:  # 确保线程安全
                        if zero_year_sharp <= 3:
                            final_result.append(rec)
                        else:
                            removed_alpha_ids.append(rec['id'])

                # 使用 ThreadPoolExecutor 并行处理
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:  # 调整 max_workers 控制并发数
                    list(tqdm(
                        executor.map(process_alpha, result_list),
                        total=total_alphas,
                        desc="筛除进度",
                        ncols=100
                    ))

                print(f'    筛除完成，筛除 alpha_ids: {removed_alpha_ids}')
            print('######### 筛除厂子形alpha #########')
        else:
            final_result = result_list

        print("count: %d"%count)
        print("pass_count: %d"%len(final_result))
        return final_result
    
    def wait_get(self, url: str, max_retries: int = 10) -> "Response":
        """
        发送带有重试机制的 GET 请求，直到成功或达到最大重试次数。
        此函数会根据服务器返回的 `Retry-After` 头信息进行等待，并在遇到 401 状态码时重新初始化配置。
        
        Args:
            url (str): 目标 URL。
            max_retries (int, optional): 最大重试次数，默认为 10。
        
        Returns:
            Response: 请求的响应对象。
        """
        retries = 0
        while retries < max_retries:
            while True:
                simulation_progress = self.session.get(url)
                if simulation_progress.headers.get("Retry-After", 0) == 0:
                    break
                time.sleep(float(simulation_progress.headers["Retry-After"]))
            if simulation_progress.status_code < 400:
                break
            else:
                time.sleep(2 ** retries)
                retries += 1
        return simulation_progress
    
    def transform(self, next_alpha_recs, region):
        output = []
        for rec in next_alpha_recs:
            
            decay = rec['decay']
            exp = rec['exp']
            output.append([exp,decay])
        output_dict = {region : output}
        return output_dict

    # def prune(self, next_alpha_recs, region, prefix, keep_num):
    #     # prefix is the datafield prefix, fnd6, mdl175 ...
    #     # keep_num is the num of top sharpe same-datafield alpha
    #     output = []
    #     num_dict = defaultdict(int)
    #     for rec in next_alpha_recs:
    #         exp = rec[1]
    #         field = exp.split(prefix)[-1].split(",")[0]
    #         sharpe = rec[2]
    #         if sharpe < 0:
    #             field = "-%s"%field
    #         if num_dict[field] < keep_num:
    #             num_dict[field] += 1
    #             decay = rec[-1]
    #             exp = rec[1]
    #             output.append([exp,decay])
    #     output_dict = {region : output}
    #     return output_dict
    
      ## 剪枝
    def prune(self, next_alpha_recs, region, prefix, keep_num):
        # prefix is the datafield prefix, fnd6, mdl175 ...
        # keep num is the num of top sharpe same-datafield alpha
        output = []
        num_dict = defaultdict(int)
        for rec in next_alpha_recs:
            # print(rec)
            exp = rec['exp']
            field = exp.split(prefix)[-1].split(",")[0]
            sharpe = rec['sharpe']
            if sharpe < 0:
                field = "-%s"%field
            if num_dict[field] < keep_num:
                num_dict[field] += 1
                decay=rec['decay']
                exp = rec['exp']
                output.append ([exp,decay])
        # output_dict = {region : output}
        return output

    def get_first_order(self, vec_fields, ops_set, region):
        alpha_set = []
        for field in vec_fields:
            alpha_set.append(field)
            for op in ops_set:
                if op == "ts_percentage":
                    alpha_set += self.ts_comp_factory(op, field, "percentage", [0.5])
                elif op == "ts_decay_exp_window":
                    alpha_set += self.ts_comp_factory(op, field, "factor", [0.5])
                elif op == "ts_moment":
                    alpha_set += self.ts_comp_factory(op, field, "k", [2, 3, 4])
                elif op == "ts_entropy":
                    alpha_set += self.ts_comp_factory(op, field, "buckets", [10])
                elif op in twin_field_ops:
                    alpha_set += self.twin_field_factory(op, field, vec_fields)
                elif op.startswith("ts_") or op == "inst_tvr":
                    alpha_set += self.ts_factory(op, field)
                elif op.startswith("group_"):
                    alpha_set += self.group_factory(op, field, region)
                elif op.startswith("vector"):
                    alpha_set += self.vector_factory(op, field)
                elif op == "signed_power":
                    alpha = "%s(%s, 2)"%(op, field)
                    alpha_set.append(alpha)
                else:
                    alpha = "%s(%s)"%(op, field)
                    alpha_set.append(alpha)
        return alpha_set
        
    def get_group_second_order_factory(self, first_order, group_ops, region):
        second_order = []
        for fo in first_order:
            for group_op in group_ops:
                second_order += self.group_factory(group_op, fo, region)
        return second_order
     
    def get_ts_second_order_factory(self, first_order, ts_ops):
        second_order = []
        for fo in first_order:
            for ts_op in ts_ops:
                second_order += self.ts_factory(ts_op, fo)
        return second_order
     
     
    def get_data_fields_csv(self, filename, prefix):
        '''
        inputs: 
        CSV file with header 'field' 
        outputs:
        A list of string
        '''
        df = pd.read_csv(filename,header=0,encoding = 'unicode_escape')
        collection = []
        for _, row in df.iterrows():
            if row['field'].startswith(prefix):
                collection.append(row['field'])
     
        return collection
     
    def ts_arith_factory(self, ts_op, arith_op, field):
        first_order = "%s(%s)"%(arith_op, field)
        second_order = self.ts_factory(ts_op, first_order)
        return second_order
     
    def arith_ts_factory(self, arith_op, ts_op, field):
        second_order = []
        first_order = self.ts_factory(ts_op, field)
        for fo in first_order:
            second_order.append("%s(%s)"%(arith_op, fo))
        return second_order
     
    def ts_group_factory(self, ts_op, group_op, field, region):
        second_order = []
        first_order = self.group_factory(group_op, field, region)
        for fo in first_order:
            second_order += self.ts_factory(ts_op, fo)
        return second_order
     
    def group_ts_factory(self, group_op, ts_op, field, region):
        second_order = []
        first_order = self.ts_factory(ts_op, field)
        for fo in first_order:
            second_order += self.group_factory(group_op, fo, region)
        return second_order
     
    def vector_factory(self, op, field):
        output = []
        vectors = ["cap"]
        
        for vector in vectors:
        
            alpha = "%s(%s, %s)"%(op, field, vector)
            output.append(alpha)
        
        return output
     
    def trade_when_factory(self, op,field,region):
        output = []
        open_events = ["ts_arg_max(volume, 5) == 0", "ts_corr(close, volume, 20) < 0",
                       "ts_corr(close, volume, 5) < 0", "ts_mean(volume,10)>ts_mean(volume,60)",
                       "group_rank(ts_std_dev(returns,60), sector) > 0.7", "ts_zscore(returns,60) > 2",
                    #    "ts_skewness(returns,120)> 0.7", 
                       "ts_arg_min(volume, 5) > 3",
                       "ts_std_dev(returns, 5) > ts_std_dev(returns, 20)",
                       "ts_arg_max(close, 5) == 0", "ts_arg_max(close, 20) == 0",
                       "ts_corr(close, volume, 5) > 0", "ts_corr(close, volume, 5) > 0.3", "ts_corr(close, volume, 5) > 0.5",
                       "ts_corr(close, volume, 20) > 0", "ts_corr(close, volume, 20) > 0.3", "ts_corr(close, volume, 20) > 0.5",
                       "ts_regression(returns, %s, 5, lag = 0, rettype = 2) > 0"%field,
                       "ts_regression(returns, %s, 20, lag = 0, rettype = 2) > 0"%field,
                       "ts_regression(returns, ts_step(20), 20, lag = 0, rettype = 2) > 0",
                       "ts_regression(returns, ts_step(5), 5, lag = 0, rettype = 2) > 0",
                       "ts_corr(close,volume,20) > 0.1",
                        "volume>adv20",
                        "(volume>adv20) && (ts_corr(close,volume,20) > 0.1)",
                        "(close>ts_mean(close,90))&&(volume>ts_mean(volume,90))",
                        "(close>ts_mean(close,10))&&(volume>ts_mean(volume,10))"]

        # exit_events = ["abs(returns) > 0.1", "-1", "days_from_last_change(ern3_pre_reptime) > 20"]
        exit_events = ["abs(returns) > 0.1", "-1"]

        usa_events = ["rank(rp_css_business) > 0.8", "ts_rank(rp_css_business, 22) > 0.8", "rank(vec_avg(mws82_sentiment)) > 0.8",
                      "ts_rank(vec_avg(mws82_sentiment),22) > 0.8", "rank(vec_avg(nws48_ssc)) > 0.8",
                      "ts_rank(vec_avg(nws48_ssc),22) > 0.8", "rank(vec_avg(mws50_ssc)) > 0.8", "ts_rank(vec_avg(mws50_ssc),22) > 0.8",
                      "ts_rank(vec_sum(scl12_alltype_buzzvec),22) > 0.9", "pcr_oi_270 < 1", "pcr_oi_270 > 1",]

        asi_events = ["rank(vec_avg(mws38_score)) > 0.8", "ts_rank(vec_avg(mws38_score),22) > 0.8"]

        eur_events = ["rank(rp_css_business) > 0.8", "ts_rank(rp_css_business, 22) > 0.8",
                      "rank(vec_avg(oth429_research_reports_fundamental_keywords_4_method_2_pos)) > 0.8",
                      "ts_rank(vec_avg(oth429_research_reports_fundamental_keywords_4_method_2_pos),22) > 0.8",
                      "rank(vec_avg(mws84_sentiment)) > 0.8", "ts_rank(vec_avg(mws84_sentiment),22) > 0.8",
                      "rank(vec_avg(mws85_sentiment)) > 0.8", "ts_rank(vec_avg(mws85_sentiment),22) > 0.8",
                      "rank(mdl110_analyst_sentiment) > 0.8", "ts_rank(mdl110_analyst_sentiment, 22) > 0.8",
                      "rank(vec_avg(nws3_scores_posnormscr)) > 0.8",
                      "ts_rank(vec_avg(nws3_scores_posnormscr),22) > 0.8",
                      "rank(vec_avg(mws36_sentiment_words_positive)) > 0.8",
                      "ts_rank(vec_avg(mws36_sentiment_words_positive),22) > 0.8"]

        glb_events = ["rank(vec_avg(mdl109_news_sent_1m)) > 0.8",
                      "ts_rank(vec_avg(mdl109_news_sent_1m),22) > 0.8",
                      "rank(vec_avg(nws20_ssc)) > 0.8",
                      "ts_rank(vec_avg(nws20_ssc),22) > 0.8",
                      "vec_avg(nws20_ssc) > 0",
                      "rank(vec_avg(nws20_bee)) > 0.8",
                      "ts_rank(vec_avg(nws20_bee),22) > 0.8",
                      "rank(vec_avg(nws20_qmb)) > 0.8",
                      "ts_rank(vec_avg(nws20_qmb),22) > 0.8"]

        chn_events = ["rank(vec_avg(oth111_xueqiunaturaldaybasicdivisionstat_senti_conform)) > 0.8",
                      "ts_rank(vec_avg(oth111_xueqiunaturaldaybasicdivisionstat_senti_conform),22) > 0.8",
                      "rank(vec_avg(oth111_gubanaturaldaydevicedivisionstat_senti_conform)) > 0.8",
                      "ts_rank(vec_avg(oth111_gubanaturaldaydevicedivisionstat_senti_conform),22) > 0.8",
                      "rank(vec_avg(oth111_baragedivisionstat_regi_senti_conform)) > 0.8",
                      "ts_rank(vec_avg(oth111_baragedivisionstat_regi_senti_conform),22) > 0.8"]

        kor_events = ["rank(vec_avg(mdl110_analyst_sentiment)) > 0.8",
                      "ts_rank(vec_avg(mdl110_analyst_sentiment),22) > 0.8",
                      "rank(vec_avg(mws38_score)) > 0.8",
                      "ts_rank(vec_avg(mws38_score),22) > 0.8"]

        twn_events = ["rank(vec_avg(mdl109_news_sent_1m)) > 0.8",
                      "ts_rank(vec_avg(mdl109_news_sent_1m),22) > 0.8",
                      "rank(rp_ess_business) > 0.8",
                      "ts_rank(rp_ess_business,22) > 0.8"]
        
        open_events_all = open_events
        if region == "USA":
            open_events_all += usa_events
        elif region == "EUR":
            open_events_all += eur_events
        elif region == "ASI":
            open_events_all += asi_events
        elif region == "GLB":
            open_events_all += glb_events
        elif region == "CHN":
            open_events_all += chn_events
        elif region == "KOR":
            open_events_all += kor_events
        elif region == "TWN":
            open_events_all += twn_events

        for oe in open_events_all:
            for ee in exit_events:
                alpha = "%s(%s, %s, %s)"%(op, oe, field, ee)
                output.append(alpha)
        return output
     
    def ts_factory(self, op, field):
        output = []
        #days = [3, 5, 10, 20, 60, 120, 240]
        days = [5, 22, 66, 120, 240]
        
        for day in days:
        
            alpha = "%s(%s, %d)"%(op, field, day)
            output.append(alpha)
        
        return output
     
    def ts_comp_factory(self, op, field, factor, paras):
        output = []
        #l1, l2 = [3, 5, 10, 20, 60, 120, 240], paras
        l1, l2 = [5, 22, 66, 240], paras
        comb = list(product(l1, l2))
        
        for day,para in comb:
            
            if type(para) == float:
                alpha = "%s(%s, %d, %s=%.1f)"%(op, field, day, factor, para)
            elif type(para) == int:
                alpha = "%s(%s, %d, %s=%d)"%(op, field, day, factor, para)
            
            output.append(alpha)
        
        return output
     
    def twin_field_factory(self, op, field, fields):
        
        output = []
        #days = [3, 5, 10, 20, 60, 120, 240]
        days = [5, 22, 66, 240]
        outset = list(set(fields) - set([field]))
        
        for day in days:
            for counterpart in outset:
                alpha = "%s(%s, %s, %d)"%(op, field, counterpart, day)
                output.append(alpha)
        
        return output
     
     
    def group_factory(self, op, field, region):
        output = []
        vectors = ["cap"] 
        
        chn_group_13 = ['pv13_h_min2_sector', 'pv13_di_6l', 'pv13_rcsed_6l', 'pv13_di_5l', 'pv13_di_4l', 
                            'pv13_di_3l', 'pv13_di_2l', 'pv13_di_1l', 'pv13_parent', 'pv13_level']
        
        
        chn_group_1 = ['sta1_top3000c30','sta1_top3000c20','sta1_top3000c10','sta1_top3000c2','sta1_top3000c5']
        
        chn_group_2 = ['sta2_top3000_fact4_c10','sta2_top2000_fact4_c50','sta2_top3000_fact3_c20']
     
        chn_group_7 = ['oth171_region_sector_long_d1_sector', 'oth171_region_sector_short_d1_sector', 
                       'oth171_sector_long_d1_sector', 'oth171_sector_short_d1_sector']
        
        hkg_group_13 = ['pv13_10_f3_g2_minvol_1m_sector', 'pv13_10_minvol_1m_sector', 'pv13_20_minvol_1m_sector', 
                        'pv13_2_minvol_1m_sector', 'pv13_5_minvol_1m_sector', 'pv13_1l_scibr', 'pv13_3l_scibr',
                        'pv13_2l_scibr', 'pv13_4l_scibr', 'pv13_5l_scibr']
        
        hkg_group_1 = ['sta1_allc50','sta1_allc5','sta1_allxjp_513_c20','sta1_top2000xjp_513_c5']
        
        hkg_group_2 = ['sta2_all_xjp_513_all_fact4_c10','sta2_top2000_xjp_513_top2000_fact3_c10',
                       'sta2_allfactor_xjp_513_13','sta2_top2000_xjp_513_top2000_fact3_c20']
        
        hkg_group_8 = ['oth455_relation_n2v_p10_q50_w5_kmeans_cluster_5',
                         'oth455_relation_n2v_p10_q50_w4_kmeans_cluster_10',
                         'oth455_relation_n2v_p10_q50_w1_kmeans_cluster_20',
                         'oth455_partner_n2v_p50_q200_w4_kmeans_cluster_5', 
                         'oth455_partner_n2v_p10_q50_w4_pca_fact3_cluster_10',
                         'oth455_customer_n2v_p50_q50_w1_kmeans_cluster_5']
        
        twn_group_13 = ['pv13_2_minvol_1m_sector','pv13_20_minvol_1m_sector','pv13_10_minvol_1m_sector',
                        'pv13_5_minvol_1m_sector','pv13_10_f3_g2_minvol_1m_sector','pv13_5_f3_g2_minvol_1m_sector',
                        'pv13_2_f4_g3_minvol_1m_sector']
        
        twn_group_1 = ['sta1_allc50','sta1_allxjp_513_c50','sta1_allxjp_513_c20','sta1_allxjp_513_c2',
                       'sta1_allc20','sta1_allxjp_513_c5','sta1_allxjp_513_c10','sta1_allc2','sta1_allc5']
        
        twn_group_2 = ['sta2_allfactor_xjp_513_0','sta2_all_xjp_513_all_fact3_c20',
                       'sta2_all_xjp_513_all_fact4_c20','sta2_all_xjp_513_all_fact4_c50']
        
        twn_group_8 = ['oth455_relation_n2v_p50_q200_w1_pca_fact1_cluster_20',
                         'oth455_relation_n2v_p10_q50_w3_kmeans_cluster_20',
                         'oth455_relation_roam_w3_pca_fact2_cluster_5',
                         'oth455_relation_n2v_p50_q50_w2_pca_fact2_cluster_10', 
                         'oth455_relation_n2v_p10_q200_w5_pca_fact2_cluster_20',
                         'oth455_relation_n2v_p50_q50_w5_kmeans_cluster_5']
        
        usa_group_13 = ['pv13_h_min2_3000_sector','pv13_r2_min20_3000_sector','pv13_r2_min2_3000_sector',
                        'pv13_r2_min2_3000_sector', 'pv13_h_min2_focused_pureplay_3000_sector']
        
        usa_group_1 = ['sta1_top3000c50','sta1_allc20','sta1_allc10','sta1_top3000c20','sta1_allc5']
        
        usa_group_2 = ['sta2_top3000_fact3_c50','sta2_top3000_fact4_c20','sta2_top3000_fact4_c10']
        
        # usa_group_3 = ['sta3_2_sector', 'sta3_3_sector', 'sta3_news_sector', 'sta3_peer_sector', 'sta3_pvgroup1_sector', 'sta3_pvgroup2_sector', 'sta3_pvgroup3_sector', 'sta3_sec_sector']
        
        # usa_group_4 = ['rsk69_01c_1m', 'rsk69_57c_1m', 'rsk69_02c_2m', 'rsk69_5c_2m', 'rsk69_02c_1m', 'rsk69_05c_2m', 'rsk69_57c_2m', 'rsk69_5c_1m', 'rsk69_05c_1m', 'rsk69_01c_2m']
        
        usa_group_5 = ['anl52_2000_backfill_d1_05c', 'anl52_3000_d1_05c', 'anl52_3000_backfill_d1_02c', 
                       'anl52_3000_backfill_d1_5c', 'anl52_3000_backfill_d1_05c', 'anl52_3000_d1_5c']
        
        # usa_group_6 = ['mdl10_group_name']
        
        # usa_group_7 = ['oth171_region_sector_long_d1_sector', 'oth171_region_sector_short_d1_sector', 'oth171_sector_long_d1_sector', 'oth171_sector_short_d1_sector']
        
        usa_group_8 = ['oth455_competitor_n2v_p10_q50_w1_kmeans_cluster_10',
                         'oth455_customer_n2v_p10_q50_w5_kmeans_cluster_10',
                         'oth455_relation_n2v_p50_q200_w5_kmeans_cluster_20',
                         'oth455_competitor_n2v_p50_q50_w3_kmeans_cluster_10', 
                         'oth455_relation_n2v_p50_q50_w3_pca_fact2_cluster_10', 
                         'oth455_partner_n2v_p10_q50_w2_pca_fact2_cluster_5',
                         'oth455_customer_n2v_p50_q50_w3_kmeans_cluster_5',
                         'oth455_competitor_n2v_p50_q200_w5_kmeans_cluster_20']
        
        
        asi_group_13 = ['pv13_20_minvol_1m_sector', 'pv13_5_f3_g2_minvol_1m_sector', 'pv13_10_f3_g2_minvol_1m_sector',
                        'pv13_2_f4_g3_minvol_1m_sector', 'pv13_10_minvol_1m_sector', 'pv13_5_minvol_1m_sector']
        
        asi_group_1 = ['sta1_allc50', 'sta1_allc10', 'sta1_minvol1mc50','sta1_minvol1mc20',
                       'sta1_minvol1m_normc20', 'sta1_minvol1m_normc50']
        
        asi_group_8 = ['oth455_partner_roam_w3_pca_fact1_cluster_5',
                       'oth455_relation_roam_w3_pca_fact1_cluster_20',
                       'oth455_relation_roam_w3_kmeans_cluster_20',
                       'oth455_relation_n2v_p10_q200_w5_pca_fact1_cluster_20',
                       'oth455_competitor_n2v_p10_q200_w1_kmeans_cluster_10']
        
        jpn_group_1 = ['sta1_alljpn_513_c5', 'sta1_alljpn_513_c50', 'sta1_alljpn_513_c2', 'sta1_alljpn_513_c20']
        
        jpn_group_2 = ['sta2_top2000_jpn_513_top2000_fact3_c20', 'sta2_all_jpn_513_all_fact1_c5',
                       'sta2_allfactor_jpn_513_9', 'sta2_all_jpn_513_all_fact1_c10']
        
        jpn_group_8 = ['oth455_customer_n2v_p50_q50_w5_kmeans_cluster_10', 
                       'oth455_customer_n2v_p50_q50_w4_kmeans_cluster_10', 
                       'oth455_customer_n2v_p50_q50_w3_kmeans_cluster_10', 
                       'oth455_customer_n2v_p50_q50_w2_kmeans_cluster_10',
                       'oth455_customer_n2v_p50_q200_w5_kmeans_cluster_10',
                       'oth455_customer_n2v_p50_q200_w5_kmeans_cluster_10']
        
        jpn_group_13 = ['pv13_2_minvol_1m_sector', 'pv13_2_f4_g3_minvol_1m_sector', 'pv13_10_minvol_1m_sector',
                        'pv13_10_f3_g2_minvol_1m_sector', 'pv13_all_delay_1_parent', 'pv13_all_delay_1_level']
        
        kor_group_13 = ['pv13_10_f3_g2_minvol_1m_sector', 'pv13_5_minvol_1m_sector', 'pv13_5_f3_g2_minvol_1m_sector',
                        'pv13_2_minvol_1m_sector', 'pv13_20_minvol_1m_sector', 'pv13_2_f4_g3_minvol_1m_sector']
        
        kor_group_1 = ['sta1_allc20','sta1_allc50','sta1_allc2','sta1_allc10','sta1_minvol1mc50',
                       'sta1_allxjp_513_c10', 'sta1_top2000xjp_513_c50']
        
        kor_group_2 =['sta2_all_xjp_513_all_fact1_c50','sta2_top2000_xjp_513_top2000_fact2_c50',
                      'sta2_all_xjp_513_all_fact4_c50','sta2_all_xjp_513_all_fact4_c5']
        
        kor_group_8 = ['oth455_relation_n2v_p50_q200_w3_pca_fact3_cluster_5',
                         'oth455_relation_n2v_p50_q50_w4_pca_fact2_cluster_10',
                         'oth455_relation_n2v_p50_q200_w5_pca_fact2_cluster_5',
                         'oth455_relation_n2v_p50_q200_w4_kmeans_cluster_10', 
                         'oth455_relation_n2v_p10_q50_w1_kmeans_cluster_10', 
                         'oth455_relation_n2v_p50_q50_w5_pca_fact1_cluster_20']
        
        eur_group_13 = ['pv13_5_sector', 'pv13_2_sector', 'pv13_v3_3l_scibr', 'pv13_v3_2l_scibr', 'pv13_2l_scibr',
                        'pv13_52_sector', 'pv13_v3_6l_scibr', 'pv13_v3_4l_scibr', 'pv13_v3_1l_scibr']
        
        eur_group_1 = ['sta1_allc10', 'sta1_allc2', 'sta1_top1200c2', 'sta1_allc20', 'sta1_top1200c10']
        
        eur_group_2 = ['sta2_top1200_fact3_c50','sta2_top1200_fact3_c20','sta2_top1200_fact4_c50']
        
        eur_group_3 = ['sta3_6_sector', 'sta3_pvgroup4_sector', 'sta3_pvgroup5_sector']
        
        eur_group_7 = ['oth171_region_sector_long_d1_sector', 'oth171_region_sector_short_d1_sector', 
                       'oth171_sector_long_d1_sector', 'oth171_sector_short_d1_sector']
        
        eur_group_8 = ['oth455_relation_n2v_p50_q200_w3_pca_fact1_cluster_5',
                         'oth455_competitor_n2v_p50_q200_w4_kmeans_cluster_20',
                         'oth455_competitor_n2v_p50_q200_w5_pca_fact1_cluster_10', 
                         'oth455_competitor_roam_w4_pca_fact2_cluster_20', 
                         'oth455_relation_n2v_p10_q200_w2_pca_fact2_cluster_20', 
                         'oth455_competitor_roam_w2_pca_fact3_cluster_20']
        
        # glb_group_13 = ["pv13_10_f2_g3_sector", "pv13_2_f3_g2_sector", "pv13_2_sector", "pv13_52_all_delay_1_sector"]
        
        # glb_group_3 = ['sta3_2_sector', 'sta3_3_sector', 'sta3_news_sector', 'sta3_peer_sector', 'sta3_pvgroup1_sector', 'sta3_pvgroup2_sector', 'sta3_pvgroup3_sector', 'sta3_sec_sector']
        
        glb_group_1 = ['sta1_allc20', 'sta1_allc10', 'sta1_allc50', 'sta1_allc5']
        
        # glb_group_2 = ['sta2_all_fact4_c50', 'sta2_all_fact4_c20', 'sta2_all_fact3_c20', 'sta2_all_fact4_c10']
        
        glb_group_13 = ['pv13_2_sector', 'pv13_10_sector', 'pv13_3l_scibr', 'pv13_2l_scibr', 'pv13_1l_scibr',
                        'pv13_52_minvol_1m_all_delay_1_sector','pv13_52_minvol_1m_sector','pv13_52_minvol_1m_sector']
        
        # glb_group_7 = ['oth171_region_sector_long_d1_sector', 'oth171_region_sector_short_d1_sector', 'oth171_sector_long_d1_sector', 'oth171_sector_short_d1_sector']  
        
        glb_group_8 = ['oth455_relation_n2v_p10_q200_w5_kmeans_cluster_5',
                         'oth455_relation_n2v_p10_q50_w2_kmeans_cluster_5',
                         'oth455_relation_n2v_p50_q200_w5_kmeans_cluster_5', 
                         'oth455_customer_n2v_p10_q50_w4_pca_fact3_cluster_20', 
                         'oth455_competitor_roam_w2_pca_fact1_cluster_10', 
                         'oth455_relation_n2v_p10_q200_w2_kmeans_cluster_5']
        
        amr_group_13 = ['pv13_4l_scibr', 'pv13_1l_scibr', 'pv13_hierarchy_min51_f1_sector',
                        'pv13_hierarchy_min2_600_sector', 'pv13_r2_min2_sector', 'pv13_h_min20_600_sector']
        
        amr_group_3 = ['sta3_news_sector', 'sta3_peer_sector', 'sta3_pvgroup1_sector', 'sta3_pvgroup2_sector',
                       'sta3_pvgroup3_sector']
        
        amr_group_8 = ['oth455_relation_roam_w1_pca_fact2_cluster_10', 
                       'oth455_competitor_n2v_p50_q50_w4_kmeans_cluster_10', 
                       'oth455_competitor_n2v_p50_q50_w3_kmeans_cluster_10', 
                       'oth455_competitor_n2v_p50_q50_w2_kmeans_cluster_10', 
                       'oth455_competitor_n2v_p50_q50_w1_kmeans_cluster_10',
                       'oth455_competitor_n2v_p50_q200_w5_kmeans_cluster_10']
        
        # group_3 = ["oth171_region_sector_long_d1_sector", "oth171_region_sector_short_d1_sector", "oth171_sector_long_d1_sector", "oth171_sector_short_d1_sector"]
        
        bps_group = "bucket(rank(fnd28_value_05480/close), range='0.2, 1, 0.2')"
        cap_group = "bucket(rank(cap), range='0.1, 1, 0.1')"
        sector_cap_group = "bucket(group_rank(cap,sector),range='0,1,0.1')"
        vol_group = "bucket(rank(ts_std_dev(ts_returns(close,1),20)),range = '0.1,1,0.1')"
        
        groups = ["market","sector", "industry", "subindustry", bps_group, cap_group, sector_cap_group]
        
        if region == "CHN":
            groups += chn_group_13 + chn_group_1 + chn_group_2 #+ group_3 
        if region == "TWN":
            groups += twn_group_13 + twn_group_1 + twn_group_2 + twn_group_8 
        if region == "ASI":
            groups += asi_group_13 + asi_group_1 + asi_group_8 
        if region == "USA":
            groups += usa_group_13 + usa_group_1 + usa_group_2 + usa_group_8 # + usa_group_3 + usa_group_4  + group_3 
            groups += usa_group_5 #+ usa_group_6 + usa_group_7
        if region == "HKG":
            groups += hkg_group_13 + hkg_group_1 + hkg_group_2 + hkg_group_8
        if region == "KOR":
            groups += kor_group_13 + kor_group_1 + kor_group_2 + kor_group_8
        if region == "EUR": 
            groups += eur_group_13 + eur_group_1 + eur_group_2 + eur_group_3 + eur_group_8 +  eur_group_7 #+ group_3 
        if region == "GLB":
            groups += glb_group_13 + glb_group_8 + glb_group_1 #+ glb_group_7 + glb_group_3 + group_3
        if region == "AMR":
            groups += amr_group_3 + amr_group_13
        if region == "JPN":
            groups += jpn_group_1 + jpn_group_2 + jpn_group_13 + jpn_group_8
            
        for group in groups:
            if op.startswith("group_vector"):
                for vector in vectors:
                    alpha = "%s(%s,%s,densify(%s))"%(op, field, vector, group)
                    output.append(alpha)
            elif op.startswith("group_percentage"):
                alpha = "%s(%s,densify(%s),percentage=0.5)"%(op, field, group)
                output.append(alpha)
            else:
                alpha = "%s(%s,densify(%s))"%(op, field, group)
                output.append(alpha)
        
        return output

    def load_task_pool(self, alpha_list: list, batch_size: int = 10, concurrent_batches: int = 8) -> list:
        """Split alpha list into pools of batches for concurrent processing."""
        pools = []
        current_pool = []
        current_batch = []
        
        for alpha in alpha_list:
            current_batch.append(alpha)
            
            if len(current_batch) >= batch_size:
                current_pool.append(current_batch)
                current_batch = []
                
                if len(current_pool) >= concurrent_batches:
                    pools.append(current_pool)
                    current_pool = []
        
        # Add any remaining batches
        if current_batch:
            current_pool.append(current_batch)
        if current_pool:
            pools.append(current_pool)
        
        self.logger.info(f"Created {len(pools)} pools with {batch_size} alphas per batch")
        return pools