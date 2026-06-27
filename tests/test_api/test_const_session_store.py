"""ConstSessionStore 单元测试。

测试消息序列化/反序列化（纯函数）和 YAML 文件 I/O。
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from api.const_session_store import (
    delete_const_session,
    deserialize_messages,
    load_all_const_sessions,
    load_const_session,
    save_const_session,
    serialize_messages,
)


class TestMessageSerialization:
    """消息序列化/反序列化纯函数测试（无需 mock）。"""

    def test_serialize_human_message(self):
        """HumanMessage → dict with type='human', content."""
        msg = HumanMessage(content="Hello, world!")
        result = serialize_messages([msg])
        assert len(result) == 1
        assert result[0]["type"] == "human"
        assert result[0]["content"] == "Hello, world!"

    def test_serialize_ai_message_with_tool_calls(self):
        """AIMessage with tool_calls → dict includes tool_calls."""
        tool_calls = [
            {"name": "get_weather", "args": {"city": "Tokyo"}, "id": "call_1"}
        ]
        msg = AIMessage(content="Let me check", tool_calls=tool_calls)
        result = serialize_messages([msg])
        assert len(result) == 1
        assert result[0]["type"] == "ai"
        assert result[0]["content"] == "Let me check"
        assert "tool_calls" in result[0]
        # AIMessage.tool_calls 自动添加 type='tool_call'
        assert result[0]["tool_calls"] == [
            {
                "name": "get_weather",
                "args": {"city": "Tokyo"},
                "id": "call_1",
                "type": "tool_call",
            }
        ]

    def test_serialize_tool_message(self):
        """ToolMessage → dict with type='tool', tool_call_id, name."""
        msg = ToolMessage(
            content="Weather is sunny",
            tool_call_id="call_1",
            name="get_weather",
        )
        result = serialize_messages([msg])
        assert len(result) == 1
        assert result[0]["type"] == "tool"
        assert result[0]["content"] == "Weather is sunny"
        assert result[0]["tool_call_id"] == "call_1"
        assert result[0]["name"] == "get_weather"

    def test_deserialize_human(self):
        """dict → HumanMessage 实例。"""
        data = [{"type": "human", "content": "Hello"}]
        result = deserialize_messages(data)
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "Hello"

    def test_deserialize_ai_with_tool_calls(self):
        """dict with tool_calls → AIMessage。"""
        tool_calls = [
            {"name": "get_weather", "args": {"city": "Tokyo"}, "id": "call_1"}
        ]
        data = [{"type": "ai", "content": "Sure!", "tool_calls": tool_calls}]
        result = deserialize_messages(data)
        assert len(result) == 1
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "Sure!"
        # AIMessage.tool_calls may be a tuple of ToolCall objects;
        # compare via dict representation.
        assert len(result[0].tool_calls) == 1
        tc = result[0].tool_calls[0]
        assert tc["name"] == "get_weather"
        assert tc["args"] == {"city": "Tokyo"}
        assert tc["id"] == "call_1"

    def test_deserialize_unknown_type_fallback(self):
        """未知 type → HumanMessage（fallback）。"""
        data = [{"type": "robot", "content": "Beep boop"}]
        result = deserialize_messages(data)
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "Beep boop"

    def test_roundtrip_mixed_messages(self):
        """Human + AI + Tool → serialize → deserialize → 内容一致。"""
        original = [
            HumanMessage(content="What's the weather?"),
            AIMessage(
                content="Let me check",
                tool_calls=[
                    {
                        "name": "get_weather",
                        "args": {"city": "Tokyo"},
                        "id": "c1",
                    }
                ],
            ),
            ToolMessage(
                content="Sunny", tool_call_id="c1", name="get_weather"
            ),
        ]
        serialized = serialize_messages(original)
        deserialized = deserialize_messages(serialized)

        assert len(deserialized) == 3

        # Human
        assert isinstance(deserialized[0], HumanMessage)
        assert deserialized[0].content == "What's the weather?"

        # AI
        assert isinstance(deserialized[1], AIMessage)
        assert deserialized[1].content == "Let me check"
        assert len(deserialized[1].tool_calls) == 1
        assert deserialized[1].tool_calls[0]["name"] == "get_weather"

        # Tool
        assert isinstance(deserialized[2], ToolMessage)
        assert deserialized[2].content == "Sunny"
        assert deserialized[2].tool_call_id == "c1"
        assert deserialized[2].name == "get_weather"


class TestConstSessionFileIO:
    """YAML 文件 I/O 测试（mock _CONST_DIR → 临时目录）。"""

    @pytest.fixture
    def const_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def patched_const_dir(self, const_dir):
        """将 _CONST_DIR 替换为临时目录的 Path。"""
        with patch("api.const_session_store._CONST_DIR", const_dir):
            yield const_dir

    def test_save_and_load(self, patched_const_dir):
        """save → 文件存在 → load 返回正确数据。"""
        sid = "test-123"
        messages = [{"type": "human", "content": "hello"}]
        save_const_session(sid, "Test", {"count": 5}, messages)

        filepath = patched_const_dir / f"{sid}.yaml"
        assert filepath.exists()

        loaded = load_const_session(filepath)
        assert loaded is not None
        assert loaded["session_id"] == sid
        assert loaded["const_name"] == "Test"
        assert loaded["metadata"] == {"count": 5}
        assert loaded["messages"] == messages
        assert "const_saved_at" in loaded

    def test_load_nonexistent(self):
        """load 不存在的文件 → None。"""
        result = load_const_session(Path("/nonexistent/file.yaml"))
        assert result is None

    def test_delete(self, patched_const_dir):
        """save → delete True → 再次 delete False。"""
        sid = "test-123"
        save_const_session(sid, "Test", {}, [])
        assert delete_const_session(sid) is True
        # 文件已删除
        filepath = patched_const_dir / f"{sid}.yaml"
        assert not filepath.exists()
        # 再次删除返回 False
        assert delete_const_session(sid) is False

    def test_load_all(self, patched_const_dir):
        """保存 2 个会话 → load_all 返回两者。"""
        save_const_session("sid1", "One", {"k": 1}, [])
        save_const_session("sid2", "Two", {"k": 2}, [])
        sessions = load_all_const_sessions()
        assert len(sessions) == 2
        sids = {s["session_id"] for s in sessions}
        assert sids == {"sid1", "sid2"}
        names = {s["const_name"] for s in sessions}
        assert names == {"One", "Two"}
