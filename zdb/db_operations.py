import sys
import os
# 将当前文件所在目录添加到Python搜索路径，确保同一目录下的模块可以被正确导入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import db_helper
from typing import Dict, Any, Tuple, List


class DataBaseOp:
    """
    数据库操作类
    """
    def __init__(self):
        self.db_helper = db_helper.PostgreSQLHelper()

    def save_com(self, table_name: str, data: Dict[str, Any]):
        """
        保存单条记录到数据库
        
        Args:
            table_name: 表名
            data: 要保存的数据字典
            
        Returns:
            bool: 操作是否成功
        """
        # 提取字段名和值，避免 SQL 注入（使用参数化查询）
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))  # %s 是 psycopg2 的参数占位符
        values = tuple(data.values())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.db_helper.execute_update(query, values)
        
    def batch_save_com(self, table_name: str, data_list: List[Dict[str, Any]]):
        """
        批量保存记录到数据库
        
        Args:
            table_name: 表名
            data_list: 要保存的数据字典列表
            
        Returns:
            bool: 操作是否成功
        """
        if not data_list:
            return True  # 空列表，视为操作成功
            
        # 检查所有记录是否有相同的字段
        first_record_keys = set(data_list[0].keys())
        if not all(set(record.keys()) == first_record_keys for record in data_list):
            raise ValueError("批量插入时所有记录必须具有相同的字段")
            
        # 提取字段名
        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(["%s"] * len(data_list[0]))
        
        # 构建事务查询列表
        queries = []
        for data in data_list:
            values = tuple(data.values())
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            queries.append({'query': query, 'params': values})
            
        # 使用事务批量执行
        return self.db_helper.execute_transaction(queries)
    def update_com(self, table_name: str,update_data: Dict[str, Any], where_condition: Tuple[str, Tuple[any, ...]]):
        """
        单条数据更新（按条件更新指定行）
        :param table_name: 目标表名
        :param update_data: 待更新的键值对（key=字段名，value=新值）
        :param where_condition: WHERE 条件（格式：(条件语句, (参数值1, 参数值2, ...))）
                            例：("stock_code = %s AND trade_date = %s", ("600000", "2025-09-06"))
        :return: 受影响的行数（int，0 表示无匹配行，1 表示更新成功）
        """
        # 构造 SET 子句（字段1 = %s, 字段2 = %s）
        set_clause = ", ".join([f"{field} = %s" for field in update_data.keys()])
        # 提取更新值（顺序与 SET 子句字段对应）
        update_values = tuple(update_data.values())
        # WHERE 条件语句和参数
        where_sql, where_values = where_condition
        # 合并所有参数（更新值 + WHERE 条件值，避免 SQL 注入）
        all_values = update_values + where_values

        # 完整 SQL
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_sql}"
        return self.db_helper.execute_update(sql, all_values)


    def save_simulate_record(self, data: Dict[str, Any]):
        """
        保存单条模拟记录到数据库
        
        Args:
            data: 要保存的模拟记录数据字典
            
        Returns:
            bool: 操作是否成功
        """
        return self.save_com("brain.alpha_simulate", data)
        
    def batch_save_similar_fields(self, data_list: List[Dict[str, Any]]):
        """
        批量保存模拟记录到数据库
        
        Args:
            data_list: 要保存的模拟记录数据字典列表
            
        Returns:
            bool: 操作是否成功
        """
        return self.batch_save_com("brain.similar_fields", data_list)

    def update_simulate_record(self, data: Dict[str, Any], batch_time, order_seq):
        """
        保存运行录到数据库
        """
        return self.update_com("brain.alpha_simulate", data, ("batch_time = %s and order_seq = %s",(batch_time, order_seq)))

    def get_simulate_record_batch(self,batch_time):
        """
        从数据库获取模拟结果
        """
        query = """
            SELECT * FROM brain.alpha_simulate 
            where batch_time = %s
            ORDER BY order_seq
        """
        params = (batch_time,)
        return self.db_helper.execute_query(query, params)


    def get_simulation_results(self,limit=10):
        """
        从数据库获取模拟结果
        """
        query = """
            SELECT * FROM simulation_results 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        params = (limit,)
        return self.db_helper.execute_query(query, params)


    def save_alpha_expression(self, expression, region, universe):
        """
        保存alpha表达式到数据库
        """
        query = """
            INSERT INTO alpha_expressions (expression, region, universe)
            VALUES (%s, %s, %s)
        """
        params = (expression, region, universe)
        return self.db_helper.execute_update(query, params)


    def get_alpha_expressions(self,limit=10):
        """
        从数据库获取alpha表达式
        """
        query = """
            SELECT * FROM alpha_expressions 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        params = (limit,)
        return self.db_helper.execute_query(query, params)


    def get_simulation_result_by_alpha_id(self, alpha_id):
        """
        根据alpha_id获取模拟结果
        """
        query = """
            SELECT * FROM simulation_results 
            WHERE alpha_id = %s
            ORDER BY created_at DESC
        """
        params = (alpha_id,)
        return self.db_helper.execute_query(query, params)


    def update_simulation_result(self, alpha_id, sharpe_ratio, returns, turnover):
        """
        更新模拟结果
        """
        query = """
            UPDATE simulation_results 
            SET sharpe_ratio = %s, returns = %s, turnover = %s
            WHERE alpha_id = %s
        """
        params = (sharpe_ratio, returns, turnover, alpha_id)
        return self.db_helper.execute_update(query, params)


    def delete_simulation_result(self, alpha_id):
        """
        删除指定alpha_id的模拟结果
        """
        query = "DELETE FROM simulation_results WHERE alpha_id = %s"
        params = (alpha_id,)
        return self.db_helper.execute_update(query, params)