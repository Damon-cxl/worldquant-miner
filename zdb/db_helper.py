import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class PostgreSQLHelper:
    """
    PostgreSQL数据库辅助操作类
    提供连接管理、CRUD操作、事务处理等常用功能
    """

    def __init__(self):
        """
        初始化数据库配置
        """
        self.host = os.getenv('DB_HOST', 'localhost')
        self.database = os.getenv('DB_NAME', 'your_database')
        self.user = os.getenv('DB_USER', 'your_username')
        self.password = os.getenv('DB_PASSWORD', 'your_password')
        self.port = os.getenv('DB_PORT', '5432')

    def get_connection(self):
        """
        创建并返回数据库连接
        """
        try:
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            return conn
        except Exception as e:
            print(f"数据库连接错误: {e}")
            return None

    def execute_query(self, query: str, params: Optional[tuple] = None, 
                      fetch_one: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        执行SELECT查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            fetch_one: 是否只获取一条记录
            
        Returns:
            查询结果列表或单条记录
        """
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params)
            
            if fetch_one:
                result = cur.fetchone()
            else:
                result = cur.fetchall()
            
            cur.close()
            conn.close()
            return result
        except Exception as e:
            print(f"查询执行错误: {e}")
            return None

    def execute_update(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        执行INSERT/UPDATE/DELETE操作
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            操作是否成功
        """
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"更新执行错误: {e}")
            conn.rollback()
            return False

    def execute_transaction(self, queries: List[Dict[str, Any]]) -> bool:
        """
        执行事务操作
        
        Args:
            queries: 包含查询和参数的字典列表
                    格式: [{'query': 'INSERT INTO ...', 'params': (...)}, ...]
                    
        Returns:
            事务是否成功
        """
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            cur = conn.cursor()
            for item in queries:
                cur.execute(item['query'], item['params'])
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"事务执行错误: {e}")
            conn.rollback()
            return False

    def init_database(self) -> bool:
        """
        初始化数据库表
        """
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            cur = conn.cursor()

            # 创建模拟结果表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS simulation_results (
                    id SERIAL PRIMARY KEY,
                    alpha_id VARCHAR(50),
                    sharpe_ratio DECIMAL(10, 4),
                    returns DECIMAL(10, 4),
                    turnover DECIMAL(10, 4),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 创建alpha表达式表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alpha_expressions (
                    id SERIAL PRIMARY KEY,
                    expression TEXT,
                    region VARCHAR(20),
                    universe VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"数据库初始化错误: {e}")
            return False


# 全局实例
db_helper = PostgreSQLHelper()