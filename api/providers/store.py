"""Provider 配置存储 — 支持 memory/YAML/SQLite 三种模式。"""

from pathlib import Path
from typing import Literal

import yaml

from api.providers import ProviderConfig


class ProviderConfigStore:
    """Provider 配置存储。

    mode='yaml': 原有行为，读写 providers.yaml（默认，向后兼容）
    mode='sqlite': 存储到 SQLite
    mode='memory': 仅内存，不持久化（用于测试）
    """

    def __init__(
        self,
        path: str | Path = "providers.yaml",
        mode: Literal["yaml", "sqlite", "memory"] = "yaml",
    ):
        self.path = Path(path)
        self._mode = mode
        self._db_store = None
        if mode == "sqlite":
            from api.database.provider_store import DatabaseProviderStore

            self._db_store = DatabaseProviderStore()

    def load_all(self) -> list[ProviderConfig]:
        if self._mode == "memory":
            return []
        if self._db_store is not None:
            return self._db_store.load_all()
        # YAML mode (original)
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return [ProviderConfig(**item) for item in raw.get("providers", [])]

    def get(self, provider_id: str) -> ProviderConfig | None:
        if self._db_store is not None:
            return self._db_store.get(provider_id)
        for c in self.load_all():
            if c.id == provider_id:
                return c
        return None

    def save(self, config: ProviderConfig) -> None:
        if self._db_store is not None:
            self._db_store.save(config)
            return
        # YAML mode
        all_configs = self.load_all()
        for i, c in enumerate(all_configs):
            if c.id == config.id:
                all_configs[i] = config
                break
        else:
            all_configs.append(config)
        self._write_all(all_configs)

    def delete(self, provider_id: str) -> bool:
        if self._db_store is not None:
            return self._db_store.delete(provider_id)
        # YAML mode
        all_configs = self.load_all()
        filtered = [c for c in all_configs if c.id != provider_id]
        if len(filtered) == len(all_configs):
            return False
        self._write_all(filtered)
        return True

    def _write_all(self, configs: list[ProviderConfig]) -> None:
        data = {"providers": [c.to_dict() for c in configs]}
        with self.path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    @property
    def is_empty(self) -> bool:
        if self._db_store is not None:
            return self._db_store.is_empty
        return not self.path.exists() or not self.load_all()

    def migrate_from_env(self) -> ProviderConfig | None:
        """从 .env 读取配置并存储到当前后端。"""
        import os

        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            return None

        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        model_name = os.getenv("MODEL_NAME", "deepseek-v4-flash")
        context_window_str = os.getenv("MODEL_CONTEXT_WINDOW", "256000")

        config = ProviderConfig(
            id="deepseek-main",
            provider_type="openai",
            label="DeepSeek",
            api_key=api_key,
            base_url=base_url,
            models=[model_name],
            enabled=True,
            context_window=int(context_window_str),
        )
        self.save(config)
        return config

    @staticmethod
    def import_from_yaml(yaml_path: str | Path) -> int:
        """从 YAML 文件导入提供商配置到 SQLite（迁移工具）。"""
        from api.database.provider_store import DatabaseProviderStore

        db_store = DatabaseProviderStore()
        yaml_store = ProviderConfigStore(path=yaml_path, mode="yaml")
        configs = yaml_store.load_all()
        if not configs:
            return 0
        return db_store.save_many(configs)
