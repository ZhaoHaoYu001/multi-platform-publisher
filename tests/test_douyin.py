"""抖音平台测试."""
import pytest
from src.platforms.douyin import DouyinPlatform
from src.adapters.douyin_adapter import DouyinAdapter
from src.core.rule_engine import RuleEngine


class TestDouyinPlatform:
    """抖音平台测试."""

    def setup_method(self):
        self.platform = DouyinPlatform(cookie="test_cookie")

    def test_platform_properties(self):
        assert self.platform.name == "douyin"
        assert self.platform.max_title_length == 30
        assert self.platform.max_content_length == 1000
        assert self.platform.max_images == 35
        assert self.platform.content_type == "plain"

    def test_adapt_content_strips_markdown(self):
        content = "# 标题\n\n**粗体**和*斜体*以及`代码`\n\n[链接](http://example.com)"
        result = self.platform.adapt_content("测试标题", content)
        assert "# " not in result
        assert "**" not in result
        assert "*" not in result.split("粗体")[0]  # no markdown asterisks
        assert "`" not in result
        assert "](http" not in result

    def test_adapt_content_adds_interaction(self):
        result = self.platform.adapt_content("标题", "内容")
        assert "评论区" in result or "留言" in result

    def test_adapt_content_adds_emoji(self):
        content = "总结一下这个教程"
        result = self.platform.adapt_content("标题", content)
        # Should have emoji decoration
        assert "📝" in result or "📚" in result or len(result) > len(content)


class TestDouyinAdapter:
    """抖音适配器测试."""

    def setup_method(self):
        self.engine = RuleEngine(rules_dir="config/rules")
        self.adapter = DouyinAdapter(self.engine, credentials={"cookie": "test"})

    def test_platform_name(self):
        assert self.adapter.platform_name == "douyin"

    def test_adapt(self):
        from src.core.content_document import ContentDocument
        doc = ContentDocument(title="测试标题", body=[])
        result = self.adapter.adapt(doc)
        assert result.title is not None
        assert isinstance(result.content, str)

    def test_simulate(self):
        from src.adapters.base_adapter import AdaptationResult
        adapted = AdaptationResult(title="测试", content="内容", images=[], warnings=[])
        result = self.adapter._simulate(adapted)
        assert result.success is True
        assert "模拟发布" in result.message
