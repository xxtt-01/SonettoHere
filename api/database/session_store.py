"""基于 SQLite 的会话持久化存储。"""

import time

from api.database import get_connection


class DatabaseSessionStore:
    """会话数据的 SQLite 持久化层。

    注意：此 store 只负责读写数据库，不维护内存状态。
    调用方（SessionManager）负责同步内存缓存。
    """

    def save_session(self, session_id: str, **kwargs) -> None:
        """创建或更新会话记录。

        Kwargs 映射到 sessions 表的列。
        """
        conn = get_connection()
        now = time.time()
        conn.execute(
            """INSERT INTO sessions (session_id, created_at, last_active, message_count,
               is_subagent, parent_session_id, sub_agent_task, is_const, const_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
               last_active=excluded.last_active,
               message_count=excluded.message_count,
               is_const=excluded.is_const,
               const_name=excluded.const_name""",
            (
                session_id,
                kwargs.get("created_at", now),
                kwargs.get("last_active", now),
                kwargs.get("message_count", 0),
                int(kwargs.get("is_subagent", False)),
                kwargs.get("parent_session_id"),
                kwargs.get("sub_agent_task"),
                int(kwargs.get("is_const", False)),
                kwargs.get("const_name", ""),
            ),
        )
        conn.commit()

    def delete_session(self, session_id: str) -> bool:
        """从数据库删除会话。返回是否删除了记录。"""
        conn = get_connection()
        cursor = conn.execute(
            "DELETE FROM sessions WHERE session_id = ?", (session_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

    def load_all_sessions(self) -> list[dict]:
        """加载所有会话记录。"""
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY last_active DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def cleanup_expired(self, ttl_seconds: int) -> int:
        """删除过期会话。返回删除数量。"""
        cutoff = time.time() - ttl_seconds
        conn = get_connection()
        cursor = conn.execute(
            "DELETE FROM sessions WHERE last_active < ? AND is_const = 0",
            (cutoff,),
        )
        conn.commit()
        return cursor.rowcount
