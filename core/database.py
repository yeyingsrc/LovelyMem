"""
数据库工具模块

提供安全的数据库连接管理，使用 context manager 防止资源泄漏。
"""
import sqlite3
import logging
from contextlib import contextmanager
from core.paths import PRESETS_DB, FAVORITES_DB

logger = logging.getLogger(__name__)


@contextmanager
def get_connection(db_path=None):
    """
    获取数据库连接的 context manager。
    
    用法:
        with get_connection(PRESETS_DB) as conn:
            c = conn.cursor()
            c.execute("SELECT ...")
    
    自动处理 commit 和 close，异常时自动 rollback。
    """
    if db_path is None:
        db_path = PRESETS_DB
    
    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(db_path, query, params=None, fetch=False):
    """
    执行单条 SQL 查询的便捷方法。
    
    Args:
        db_path: 数据库文件路径
        query: SQL 查询语句
        params: 查询参数（元组或列表）
        fetch: 是否返回查询结果
    
    Returns:
        如果 fetch=True，返回查询结果列表；否则返回 None。
    """
    with get_connection(db_path) as conn:
        c = conn.cursor()
        if params:
            c.execute(query, params)
        else:
            c.execute(query)
        
        if fetch:
            return c.fetchall()
        return None


def ensure_table(db_path, table_name, schema):
    """
    确保表存在，如果不存在则创建。
    
    Args:
        db_path: 数据库文件路径
        table_name: 表名
        schema: 列定义字符串，如 "name TEXT PRIMARY KEY, value TEXT"
    """
    with get_connection(db_path) as conn:
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
