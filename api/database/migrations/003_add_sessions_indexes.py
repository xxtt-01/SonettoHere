"""003：添加 sessions 表清理查询索引。"""

CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_sessions_cleanup
    ON sessions(last_active, is_const);
"""


def run(conn):
    conn.execute(CREATE_INDEX)
    conn.commit()
