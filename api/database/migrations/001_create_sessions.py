"""001：创建会话表 — 替换 SessionManager 的内存存储。"""

CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    last_active REAL NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    is_subagent INTEGER NOT NULL DEFAULT 0,
    parent_session_id TEXT,
    sub_agent_task TEXT,
    is_const INTEGER NOT NULL DEFAULT 0,
    const_name TEXT DEFAULT ''
);
"""

CREATE_SESSION_MESSAGES = """
CREATE TABLE IF NOT EXISTS session_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_call_id TEXT,
    tool_name TEXT,
    tool_calls_json TEXT,
    additional_kwargs_json TEXT,
    created_at REAL NOT NULL DEFAULT (strftime('%s', 'now'))
);
"""

CREATE_SESSION_MESSAGES_INDEX = """
CREATE INDEX IF NOT EXISTS idx_session_messages_sid
    ON session_messages(session_id);
"""


def run(conn):
    conn.execute(CREATE_SESSIONS)
    conn.execute(CREATE_SESSION_MESSAGES)
    conn.execute(CREATE_SESSION_MESSAGES_INDEX)
    conn.commit()
