"""Provider 配置存储测试。"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from api.providers import ProviderConfig
from api.providers.store import ProviderConfigStore


class TestProviderStoreYamlMode:
    """YAML 模式（原始行为）向后兼容测试。"""

    @pytest.fixture
    def yaml_path(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d) / "providers.yaml"

    def test_is_empty_on_nonexistent(self, yaml_path):
        store = ProviderConfigStore(path=str(yaml_path), mode="yaml")
        assert store.is_empty

    def test_save_and_load(self, yaml_path):
        store = ProviderConfigStore(path=str(yaml_path), mode="yaml")
        config = ProviderConfig(
            id="test-1", provider_type="openai", label="Test",
            api_key="sk-test", base_url="https://test.com/v1",
        )
        store.save(config)
        loaded = store.load_all()
        assert len(loaded) == 1
        assert loaded[0].id == "test-1"
        assert loaded[0].api_key == "sk-test"

    def test_delete(self, yaml_path):
        store = ProviderConfigStore(path=str(yaml_path), mode="yaml")
        store.save(ProviderConfig(id="del-me", provider_type="openai", label="X",
                    api_key="k", base_url="https://x.com"))
        assert store.delete("del-me") is True
        assert store.delete("nonexistent") is False


class TestProviderStoreSqliteMode:
    """SQLite 模式测试。"""

    @pytest.fixture
    def sqlite_store(self):
        with tempfile.TemporaryDirectory() as d:
            db_path = Path(d) / "test.db"
            with patch("api.database.DB_PATH", db_path):
                from api.database import close_connection, get_connection
                from api.database.migrations import run_migrations
                conn = get_connection()
                run_migrations(conn)
                close_connection()
                yield ProviderConfigStore(mode="sqlite")
                close_connection()

    def test_save_and_load(self, sqlite_store):
        store = sqlite_store
        config = ProviderConfig(
            id="sqlite-1", provider_type="openai", label="SQLite Test",
            api_key="sk-sqlite", base_url="https://sqlite.test/v1",
            models=["gpt-4"],
        )
        store.save(config)
        loaded = store.load_all()
        assert len(loaded) == 1
        assert loaded[0].id == "sqlite-1"
        assert loaded[0].api_key == "sk-sqlite"
        assert loaded[0].models == ["gpt-4"]

    def test_get(self, sqlite_store):
        store = sqlite_store
        store.save(ProviderConfig(id="get-test", provider_type="openai", label="Get",
                    api_key="k", base_url="https://x.com"))
        result = store.get("get-test")
        assert result is not None
        assert result.id == "get-test"
        assert store.get("nonexistent") is None

    def test_delete(self, sqlite_store):
        store = sqlite_store
        store.save(ProviderConfig(id="del", provider_type="openai", label="D",
                    api_key="k", base_url="https://x.com"))
        assert store.delete("del") is True
        assert store.delete("del") is False

    def test_is_empty(self, sqlite_store):
        assert sqlite_store.is_empty
        sqlite_store.save(ProviderConfig(id="e1", provider_type="openai",
                            label="E", api_key="k", base_url="https://x.com"))
        assert not sqlite_store.is_empty

    def test_memory_mode_empty(self):
        """memory 模式始终返回空列表。"""
        store = ProviderConfigStore(mode="memory")
        assert store.is_empty
        assert store.load_all() == []


class TestImportFromYaml:
    """YAML → SQLite 导入测试。"""

    def test_import(self):
        with tempfile.TemporaryDirectory() as d:
            db_path = Path(d) / "test.db"
            yaml_p = Path(d) / "providers.yaml"

            # 先写 YAML
            import yaml
            yaml_data = {"providers": [{
                "id": "imported", "provider_type": "openai", "label": "Imported",
                "api_key": "sk-import", "base_url": "https://import.test/v1",
            }]}
            with open(yaml_p, "w", encoding="utf-8") as f:
                yaml.dump(yaml_data, f)

            with patch("api.database.DB_PATH", db_path):
                from api.database import close_connection, get_connection
                from api.database.migrations import run_migrations
                conn = get_connection()
                run_migrations(conn)
                close_connection()

                count = ProviderConfigStore.import_from_yaml(str(yaml_p))
                assert count == 1

                store = ProviderConfigStore(mode="sqlite")
                assert not store.is_empty
                assert store.get("imported") is not None
                close_connection()
