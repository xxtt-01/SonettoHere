"""数据库连接管理 — 线程本地 SQLite 连接。"""

import sqlite3
import threading
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "sonetto.db"

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """获取当前线程的数据库连接（线程本地单例）。"""
    if not hasattr(_local, "conn") or _local.conn is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return _local.conn


def close_connection():
    """关闭当前线程的数据库连接。"""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None


def verify_connection() -> bool:
    """验证当前数据库连接是否有效。"""
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        return True
    except Exception:
        return False
