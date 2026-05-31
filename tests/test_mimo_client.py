"""MiMo API 客户端测试."""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.ai.mimo_client import ChatMessage, ChatResponse, MiMoClient


class TestChatMessage:
    def test_create_message(self):
        msg = ChatMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"


class TestChatResponse:
    def test_default_values(self):
        resp = ChatResponse()
        assert resp.content == ""
        assert resp.model == ""
        assert resp.usage == {}

    def test_with_values(self):
        resp = ChatResponse(content="Hi", model="mimo-v2.5-pro", usage={"input_tokens": 10})
        assert resp.content == "Hi"
        assert resp.model == "mimo-v2.5-pro"


class TestMiMoClient:
    def test_init_defaults(self):
        client = MiMoClient()
        assert client.model == "mimo-v2.5-pro"
        assert client.temperature == 0.6
        assert client.max_tokens == 4096

    def test_init_custom(self):
        client = MiMoClient(api_key="test-key", base_url="https://example.com", model="custom")
        assert client.api_key == "test-key"
        assert client.base_url == "https://example.com"
        assert client.model == "custom"

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

    def test_chat_simple_with_mock(self):
        client = MiMoClient(api_key="test", base_url="https://test.com")
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="response text")]
        mock_response.model = "mimo-v2.5-pro"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)

        mock_anthropic_client = MagicMock()
        mock_anthropic_client.messages.create.return_value = mock_response
        client._client = mock_anthropic_client
        client._available = True

        result = client.chat_simple("hello", "you are helpful")
        assert result == "response text"

        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args.kwargs["system"] == "you are helpful"
        assert call_args.kwargs["messages"] == [{"role": "user", "content": "hello"}]
