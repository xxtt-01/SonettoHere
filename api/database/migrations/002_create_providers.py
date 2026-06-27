"""002：创建提供商配置表。"""

CREATE_PROVIDERS = """
CREATE TABLE IF NOT EXISTS providers (
    id TEXT PRIMARY KEY,
    provider_type TEXT NOT NULL DEFAULT 'openai',
    label TEXT NOT NULL DEFAULT '',
    api_key TEXT NOT NULL DEFAULT '',
    base_url TEXT NOT NULL DEFAULT '',
    models_json TEXT NOT NULL DEFAULT '[]',
    enabled INTEGER NOT NULL DEFAULT 1,
    context_window INTEGER NOT NULL DEFAULT 256000,
    created_at REAL NOT NULL DEFAULT (julianday('now')),
    updated_at REAL NOT NULL DEFAULT (julianday('now'))
);
"""


def run(conn):
    conn.execute(CREATE_PROVIDERS)
    conn.commit()
