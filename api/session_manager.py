"""会话状态管理 — 多会话隔离 + TTL 过期清理。"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph


@dataclass
class SessionState:
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    message_count: int = 0
    _active_task: asyncio.Task | None = field(default=None, repr=False)
    checkpointer: MemorySaver = field(default_factory=MemorySaver)
    _graph: CompiledStateGraph | None = field(default=None, repr=False)
    auto_approve: bool = False

    # ── Sub-agent 字段 ─────────────────────────────────────
    is_subagent: bool = False
    parent_session_id: str | None = None
    _sub_agent_task: str | None = field(default=None, repr=False)
    _pending_result: asyncio.Future | None = field(default=None, repr=False)

    # ── Const 固定会话字段 ──────────────────────────────────
    is_const: bool = False
    const_name: str = ""


class SessionManager:
    """会话管理器。

    mode='memory': 原有行为，仅内存（默认，向后兼容）
    mode='sqlite': 内存 + SQLite 持久化
    """

    def __init__(
        self,
        ttl_seconds: int = 1800,
        mode: Literal["memory", "sqlite"] = "memory",
    ) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._ttl = ttl_seconds
        self._mode = mode

        self._db_store = None
        if mode == "sqlite":
            from api.database.session_store import DatabaseSessionStore

            self._db_store = DatabaseSessionStore()
            self._load_from_db()

    # ── 数据库恢复 ──────────────────────────────────────────

    def _load_from_db(self) -> None:
        """从 SQLite 加载所有会话到内存。"""
        if self._db_store is None:
            return
        for row in self._db_store.load_all_sessions():
            session = SessionState(
                session_id=row["session_id"],
                created_at=row["created_at"],
                last_active=row["last_active"],
                message_count=row["message_count"],
                is_subagent=bool(row["is_subagent"]),
                parent_session_id=row.get("parent_session_id"),
                is_const=bool(row["is_const"]),
                const_name=row.get("const_name", ""),
            )
            self._sessions[session.session_id] = session

    # ── CRUD ────────────────────────────────────────────────

    def create(self) -> SessionState:
        session_id = uuid.uuid4().hex
        session = SessionState(session_id=session_id)
        self._sessions[session_id] = session

        if self._db_store:
            self._db_store.save_session(
                session_id=session_id,
                created_at=session.created_at,
                last_active=session.last_active,
                message_count=session.message_count,
            )
        return session

    def create_sub_session(
        self,
        task: str,
        parent_session_id: str | None = None,
    ) -> SessionState:
        """创建 sub-agent 会话，携带任务文本和 pending future。"""
        session_id = uuid.uuid4().hex
        session = SessionState(
            session_id=session_id,
            is_subagent=True,
            parent_session_id=parent_session_id,
            _sub_agent_task=task,
            _pending_result=asyncio.Future(),
        )
        self._sessions[session_id] = session

        if self._db_store:
            self._db_store.save_session(
                session_id=session_id,
                created_at=session.created_at,
                last_active=session.last_active,
                is_subagent=True,
                parent_session_id=parent_session_id,
                sub_agent_task=task,
            )
        return session

    def get(self, session_id: str) -> SessionState | None:
        session = self._sessions.get(session_id)
        if session is not None:
            session.last_active = time.time()
        return session

    def get_or_create(self, session_id: str) -> SessionState:
        session = self.get(session_id)
        if session is None:
            session = SessionState(session_id=session_id)
            self._sessions[session_id] = session
            if self._db_store:
                self._db_store.save_session(
                    session_id=session_id,
                    created_at=session.created_at,
                    last_active=session.last_active,
                    message_count=session.message_count,
                )
        return session

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            if self._db_store:
                self._db_store.delete_session(session_id)
            return True
        return False

    def list_sessions(self) -> list[dict]:
        result = []
        for s in self._sessions.values():
            has_active = s._active_task is not None and not s._active_task.done()
            result.append(
                {
                    "session_id": s.session_id,
                    "message_count": s.message_count,
                    "created_at": s.created_at,
                    "last_active": s.last_active,
                    "has_active_agent": has_active,
                    "is_subagent": s.is_subagent,
                    "is_const": s.is_const,
                    "const_name": s.const_name,
                }
            )
        result.sort(key=lambda x: x["last_active"], reverse=True)
        return result

    def cleanup_expired(self) -> int:
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items() if now - s.last_active > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]

        db_cleaned = 0
        if self._db_store:
            db_cleaned = self._db_store.cleanup_expired(self._ttl)
        return max(len(expired), db_cleaned)
