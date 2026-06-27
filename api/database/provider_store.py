"""基于 SQLite 的 Provider 配置存储。"""

import json
import time

from api.database import get_connection
from api.providers import ProviderConfig


class DatabaseProviderStore:
    """Provider 配置的 SQLite 持久化存储。"""

    def load_all(self) -> list[ProviderConfig]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM providers ORDER BY label"
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["models"] = json.loads(d.pop("models_json", "[]"))
            d.pop("created_at", None)
            d.pop("updated_at", None)
            d["enabled"] = bool(d["enabled"])
            result.append(ProviderConfig(**d))
        return result

    def get(self, provider_id: str) -> ProviderConfig | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM providers WHERE id = ?", (provider_id,)
        ).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["models"] = json.loads(d.pop("models_json", "[]"))
        d.pop("created_at", None)
        d.pop("updated_at", None)
        d["enabled"] = bool(d["enabled"])
        return ProviderConfig(**d)

    def save(self, config: ProviderConfig) -> None:
        conn = get_connection()
        conn.execute(
            """INSERT INTO providers (id, provider_type, label, api_key, base_url,
               models_json, enabled, context_window, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
               provider_type=excluded.provider_type,
               label=excluded.label,
               api_key=excluded.api_key,
               base_url=excluded.base_url,
               models_json=excluded.models_json,
               enabled=excluded.enabled,
               context_window=excluded.context_window,
               updated_at=excluded.updated_at""",
            (
                config.id,
                config.provider_type,
                config.label,
                config.api_key,
                config.base_url,
                json.dumps(config.models),
                int(config.enabled),
                config.context_window,
                time.time(),
            ),
        )
        conn.commit()

    def delete(self, provider_id: str) -> bool:
        conn = get_connection()
        cursor = conn.execute(
            "DELETE FROM providers WHERE id = ?", (provider_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

    @property
    def is_empty(self) -> bool:
        conn = get_connection()
        row = conn.execute("SELECT COUNT(*) as cnt FROM providers").fetchone()
        return row["cnt"] == 0
