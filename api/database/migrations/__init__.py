"""迁移运行器 — 自动发现并执行未运行的迁移。"""

import importlib
import re
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent

CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS _migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _parse_version(stem: str) -> int | None:
    """从文件名 stem（如 '001_create_sessions'）中提取数字版本号。"""
    m = re.match(r"(\d+)", stem)
    return int(m.group(1)) if m else None


def run_migrations(conn: sqlite3.Connection) -> list[int]:
    """运行所有未执行的迁移。返回已应用的版本号列表。"""
    conn.execute(CREATE_MIGRATIONS_TABLE)
    existing = {row["version"] for row in
                conn.execute("SELECT version FROM _migrations").fetchall()}

    # 发现迁移文件（数字前缀的 .py 文件，如 001_create_sessions.py）
    migrations: list[tuple[int, str]] = []
    for p in MIGRATIONS_DIR.glob("[0-9]*.py"):
        v = _parse_version(p.stem)
        if v is not None:
            migrations.append((v, p.stem))

    migrations.sort(key=lambda x: x[0])

    applied_versions = []
    for version, stem in migrations:
        if version not in existing:
            module = importlib.import_module(f"api.database.migrations.{stem}")
            module.run(conn)
            conn.execute(
                "INSERT INTO _migrations (version) VALUES (?)",
                (version,),
            )
            applied_versions.append(version)

    if applied_versions:
        conn.commit()
    return applied_versions
