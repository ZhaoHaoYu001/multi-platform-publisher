"""平台适配器层测试."""

import pytest
from unittest.mock import MagicMock, patch

from src.core.content_document import ContentDocument, ContentSection, ImageRef
from src.core.platform_base import PublishMode, PublishResult
from src.core.rule_engine import RuleEngine
from src.adapters.base_adapter import PlatformAdapter, AdaptationResult
from src.adapters.registry import AdapterRegistry
from src.adapters.wechat_adapter import WechatAdapter
from src.adapters.zhihu_adapter import ZhihuAdapter
from src.adapters.bilibili_adapter import BilibiliAdapter
from src.adapters.xiaohongshu_adapter import XiaohongshuAdapter


# 规则文件目录
import os
RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "config", "rules")


class TestAdaptationResult:
    """AdaptationResult 数据类测试."""

    def test_create_default(self):
        result = AdaptationResult(title="t", content="c")
        assert result.title == "t"
        assert result.content == "c"
        assert result.images == []
        assert result.warnings == []


class TestPlatformAdapter:
    """PlatformAdapter 基类测试."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)

    def test_adapt_title(self):
        adapter = WechatAdapter(self.engine, {})
        doc = ContentDocument(title="短标题", body=[
            ContentSection(section_type="paragraph", text="内容")
        ])
        result = adapter.adapt(doc)
        assert result.title == "短标题"

    def test_adapt_long_title(self):
        adapter = WechatAdapter(self.engine, {})
        doc = ContentDocument(
            title="这是一个超过六十四字符的标题用来测试微信公众号的标题截断功能是否正常工作这是一个很长很长的标题需要超过六十四个字符才能触发截断逻辑",
            body=[ContentSection(section_type="paragraph", text="内容")],
        )
        result = adapter.adapt(doc)
        assert len(result.title) <= 64

    def test_adapt_content_not_empty(self):
        adapter = WechatAdapter(self.engine, {})
        doc = ContentDocument(
            title="标题",
            body=[ContentSection(section_type="paragraph", text="正文内容")],
        )
        result = adapter.adapt(doc)
        assert len(result.content) > 0

    def test_simulate_mode(self):
        adapter = WechatAdapter(self.engine, {})
        doc = ContentDocument(
            title="标题",
            body=[ContentSection(section_type="paragraph", text="内容")],
        )
        result = adapter.publish(doc, [], PublishMode.SIMULATE)
        assert result.success is True
        assert "模拟发布" in result.message

    def test_simulate_with_warnings(self):
        adapter = WechatAdapter(self.engine, {})
        doc = ContentDocument(
            title="这是一个超过六十四字符的标题用来测试微信公众号的标题截断功能是否正常工作这是一个很长很长的标题需要超过六十四个字符才能触发截断逻辑",
            body=[ContentSection(section_type="paragraph", text="内容")],
        )
        result = adapter.publish(doc, [], PublishMode.SIMULATE)
        assert result.success is True


class TestWechatAdapter:
    """WechatAdapter 测试."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)

    def test_platform_name(self):
        adapter = WechatAdapter(self.engine, {})
        assert adapter.platform_name == "wechat"

    @patch("src.api.wechat_api.WechatAPI")
    def test_deliver_success(self, mock_api_cls):
        mock_api = MagicMock()
        mock_api.publish_article.return_value = {"url": "https://mp.weixin.qq.com/s/xxx"}
        mock_api_cls.return_value = mock_api

        adapter = WechatAdapter(self.engine, {"app_id": "test", "app_secret": "test"})
        adapted = AdaptationResult(title="标题", content="内容")
        result = adapter.deliver(adapted, [])
        assert result.success is True

    def test_deliver_no_credentials(self):
        adapter = WechatAdapter(self.engine, {})
        adapted = AdaptationResult(title="标题", content="内容")
        # 无凭证时 deliver 应该尝试调用 API（可能失败，但不应崩溃）
        result = adapter.deliver(adapted, [])
        # 无论成功失败，都应该返回 PublishResult
        assert isinstance(result, PublishResult)


class TestAdapterRegistry:
    """AdapterRegistry 测试."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)
        self.registry = AdapterRegistry(self.engine)

    def test_register_and_get(self):
        self.registry.register("wechat", WechatAdapter)
        adapter = self.registry.get("wechat")
        assert adapter is not None
        assert adapter.platform_name == "wechat"

    def test_get_nonexistent(self):
        adapter = self.registry.get("nonexistent")
        assert adapter is None

    def test_list_platforms(self):
        self.registry.register("wechat", WechatAdapter)
        self.registry.register("zhihu", ZhihuAdapter)
        platforms = self.registry.list_platforms()
        assert "wechat" in platforms
        assert "zhihu" in platforms

    def test_has_platform(self):
        self.registry.register("wechat", WechatAdapter)
        assert self.registry.has_platform("wechat") is True
        assert self.registry.has_platform("zhihu") is False

    def test_get_with_credentials(self):
        self.registry.register("wechat", WechatAdapter)
        adapter = self.registry.get("wechat", credentials={"app_id": "test"})
        assert adapter is not None
        assert adapter._credentials.get("app_id") == "test"


class TestAllAdaptersExist:
    """验证所有适配器都可正确实例化."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)

    def test_wechat_adapter(self):
        adapter = WechatAdapter(self.engine, {})
        assert adapter.platform_name == "wechat"

    def test_zhihu_adapter(self):
        adapter = ZhihuAdapter(self.engine, {})
        assert adapter.platform_name == "zhihu"

    def test_bilibili_adapter(self):
        adapter = BilibiliAdapter(self.engine, {})
        assert adapter.platform_name == "bilibili"

    def test_xiaohongshu_adapter(self):
        adapter = XiaohongshuAdapter(self.engine, {})
        assert adapter.platform_name == "xiaohongshu"

    def test_all_adapters_have_deliver(self):
        for cls in [WechatAdapter, ZhihuAdapter, BilibiliAdapter, XiaohongshuAdapter]:
            adapter = cls(self.engine, {})
            assert hasattr(adapter, "deliver")
            assert callable(adapter.deliver)
