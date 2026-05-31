"""微博平台测试."""
import pytest
from src.platforms.weibo import WeiboPlatform
from src.adapters.weibo_adapter import WeiboAdapter
from src.core.rule_engine import RuleEngine


class TestWeiboPlatform:
    """微博平台测试."""

    def setup_method(self):
        self.platform = WeiboPlatform(cookie="test_cookie")

    def test_platform_properties(self):
        assert self.platform.name == "weibo"
        assert self.platform.max_title_length == 32
        assert self.platform.max_content_length == 2000
        assert self.platform.max_images == 18
        assert self.platform.content_type == "plain"

    def test_adapt_content_strips_markdown(self):
        content = "# 标题\n\n**粗体**和*斜体*\n\n- 列表项"
        result = self.platform.adapt_content("测试标题", content)
        assert "# " not in result
        assert "**" not in result
        assert "- " not in result

    def test_adapt_content_bullet_points(self):
        content = "- 第一点\n- 第二点"
        result = self.platform.adapt_content("标题", content)
        assert "•" in result

    def test_adapt_content_no_images(self):
        content = "![图片](image.jpg)"
        result = self.platform.adapt_content("标题", content)
        assert "![" not in result


class TestWeiboAdapter:
    """微博适配器测试."""

    def setup_method(self):
        self.engine = RuleEngine(rules_dir="config/rules")
        self.adapter = WeiboAdapter(self.engine, credentials={"cookie": "test"})

    def test_platform_name(self):
        assert self.adapter.platform_name == "weibo"

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
