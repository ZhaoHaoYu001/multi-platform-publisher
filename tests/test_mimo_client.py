"""MiMo API 客户端测试."""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.ai.mimo_client import ChatMessage, ChatResponse, MiMoClient


class TestChatMessage:
    """ChatMessage 数据类测试."""

    def test_create_message(self):
        msg = ChatMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_system_message(self):
        msg = ChatMessage(role="system", content="You are a helpful assistant.")
        assert msg.role == "system"


class TestChatResponse:
    """ChatResponse 数据类测试."""

    def test_default_values(self):
        resp = ChatResponse()
        assert resp.content == ""
        assert resp.model == ""
        assert resp.usage == {}
        assert resp.finish_reason == ""

    def test_with_values(self):
        resp = ChatResponse(
            content="Hello!",
            model="MiMo-7B-RL",
            usage={"total_tokens": 100},
            finish_reason="stop",
        )
        assert resp.content == "Hello!"
        assert resp.model == "MiMo-7B-RL"


class TestMiMoClient:
    """MiMoClient 测试."""

    def test_init_defaults(self):
        client = MiMoClient()
        assert client.model == "MiMo-7B-RL"
        assert client.temperature == 0.6
        assert client.top_p == 0.95
        assert client.max_tokens == 4096

    def test_init_custom(self):
        client = MiMoClient(
            api_key="test-key",
            base_url="https://example.com/v1",
            model="custom-model",
            temperature=0.8,
        )
        assert client.api_key == "test-key"
        assert client.base_url == "https://example.com/v1"
        assert client.model == "custom-model"
        assert client.temperature == 0.8

    @patch.dict(os.environ, {"MIMO_API_KEY": "", "MIMO_BASE_URL": ""})
    def test_not_available_without_key(self):
        client = MiMoClient()
        assert client.is_available is False

    def test_chat_without_client_raises(self):
        client = MiMoClient(api_key="")
        client._available = None
        client._client = None
        with pytest.raises(RuntimeError, match="不可用"):
            client.chat([ChatMessage(role="user", content="hello")])

    def test_chat_simple_structure(self):
        client = MiMoClient(api_key="test")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "test"
        mock_response.usage = None

        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response

        client._client = mock_openai_client
        client._available = True

        result = client.chat_simple("hello", "you are helpful")
        assert result == "response"

        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
