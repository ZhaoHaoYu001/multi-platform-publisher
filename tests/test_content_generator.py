"""AI 内容生成器测试."""

from unittest.mock import MagicMock, patch

import pytest

from src.ai.content_generator import (
    ContentGenerator,
    GeneratedContent,
    STYLES,
    PLATFORM_TRAITS,
)
from src.ai.mimo_client import ChatResponse, MiMoClient


class TestGeneratedContent:
    """GeneratedContent 数据类测试."""

    def test_default_values(self):
        content = GeneratedContent()
        assert content.title == ""
        assert content.content == ""
        assert content.tags == []
        assert content.summary == ""

    def test_with_values(self):
        content = GeneratedContent(
            title="Test Title",
            content="# Hello\n\nWorld",
            tags=["test", "demo"],
            summary="A test article",
        )
        assert content.title == "Test Title"
        assert len(content.tags) == 2


class TestStyles:
    """内容风格定义测试."""

    def test_all_styles_exist(self):
        expected = ["tech-tutorial", "product-review", "daily-share", "industry-analysis", "general"]
        for style in expected:
            assert style in STYLES

    def test_style_structure(self):
        for key, style in STYLES.items():
            assert "name" in style
            assert "description" in style
            assert "instruction" in style


class TestPlatformTraits:
    """平台特性定义测试."""

    def test_all_platforms_exist(self):
        expected = ["wechat", "zhihu", "bilibili", "xiaohongshu", "douyin", "weibo"]
        for platform in expected:
            assert platform in PLATFORM_TRAITS


class TestContentGenerator:
    """ContentGenerator 测试."""

    def test_init_default(self):
        gen = ContentGenerator()
        assert gen.client is not None

    def test_is_available(self):
        mock_client = MagicMock(spec=MiMoClient)
        mock_client.is_available = True
        gen = ContentGenerator(client=mock_client)
        assert gen.is_available is True

    def test_generate_empty_prompt_raises(self):
        mock_client = MagicMock(spec=MiMoClient)
        gen = ContentGenerator(client=mock_client)
        with pytest.raises(ValueError, match="不能为空"):
            gen.generate("")

    def test_generate_invalid_style_raises(self):
        mock_client = MagicMock(spec=MiMoClient)
        gen = ContentGenerator(client=mock_client)
        with pytest.raises(ValueError, match="不支持的内容风格"):
            gen.generate("test", style="invalid-style")

    def test_generate_invalid_platform_raises(self):
        mock_client = MagicMock(spec=MiMoClient)
        gen = ContentGenerator(client=mock_client)
        with pytest.raises(ValueError, match="不支持的平台"):
            gen.generate("test", target_platform="invalid-platform")

    def test_generate_success(self):
        import json
        mock_client = MagicMock(spec=MiMoClient)
        resp_data = {"title": "Test", "content": "# Hello World", "tags": ["test"], "summary": "A test"}
        mock_client.chat.return_value = ChatResponse(
            content=json.dumps(resp_data, ensure_ascii=False),
            model="MiMo-7B-RL",
        )
        gen = ContentGenerator(client=mock_client)
        result = gen.generate("write a test article", style="general")
        assert result.title == "Test"
        assert result.content
    def test_generate_with_platform(self):
        mock_client = MagicMock(spec=MiMoClient)
        mock_client.chat.return_value = ChatResponse(
            content='{"title": "Zhihu", "content": "Content", "tags": [], "summary": ""}',
        )
        gen = ContentGenerator(client=mock_client)
        result = gen.generate("test", target_platform="zhihu")
        assert result.target_platform == "zhihu"

    def test_generate_for_platforms(self):
        mock_client = MagicMock(spec=MiMoClient)
        mock_client.chat.return_value = ChatResponse(
            content='{"title": "Test", "content": "Content", "tags": [], "summary": ""}',
        )
        gen = ContentGenerator(client=mock_client)
        results = gen.generate_for_platforms("test", platforms=["zhihu", "bilibili"])
        assert len(results) == 2
        assert "zhihu" in results
        assert "bilibili" in results

    def test_list_styles(self):
        styles = ContentGenerator.list_styles()
        assert "general" in styles

    def test_list_platforms(self):
        platforms = ContentGenerator.list_platforms()
        assert "wechat" in platforms


class TestParseResponse:
    """_parse_response 测试."""

    def test_valid_json(self):
        text = '{"title": "Test", "content": "Hello", "tags": ["a"], "summary": "s"}'
        result = ContentGenerator._parse_response(text)
        assert result["title"] == "Test"

    def test_json_in_code_block(self):
        text = '```json\n{"title": "Test", "content": "Hello", "tags": [], "summary": ""}\n```'
        result = ContentGenerator._parse_response(text)
        assert result["title"] == "Test"

    def test_json_with_extra_text(self):
        text = 'Here:\n{"title": "Test", "content": "Hello", "tags": [], "summary": ""}\nDone.'
        result = ContentGenerator._parse_response(text)
        assert result["title"] == "Test"

    def test_invalid_json_fallback(self):
        text = "This is not JSON"
        result = ContentGenerator._parse_response(text)
        assert result["content"] == text
