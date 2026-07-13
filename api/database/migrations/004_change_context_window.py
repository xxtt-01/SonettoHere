"""004：providers 表 context_window → model_context_windows TEXT。"""

ALTER_PROVIDERS = """
ALTER TABLE providers RENAME COLUMN context_window TO model_context_windows;
"""


def run(conn):
    # SQLite 不支持 DROP COLUMN，但支持 RENAME COLUMN
    try:
        conn.execute(ALTER_PROVIDERS)
    except Exception:
        pass  # 可能已经迁移过
    # 将旧整数列转为 TEXT（JSON 格式），默认空对象
    try:
        conn.execute(
            "UPDATE providers SET model_context_windows = '{}' "
            "WHERE model_context_windows IS NULL "
            "OR typeof(model_context_windows) = 'integer'"
        )
    except Exception:
        pass
    conn.commit()
