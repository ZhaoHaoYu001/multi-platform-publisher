"""平台基类测试模块."""

import pytest
from datetime import datetime

from src.core.platform_base import PlatformBase, PublishMode, PublishResult


class MockPlatform(PlatformBase):
    """模拟平台实现，用于测试."""

    name = "mock"
    max_title_length = 50
    max_content_length = 1000
    max_images = 5
    content_type = "richtext"

    def _do_publish(self, title, content, images, **kwargs):
        """模拟发布实现."""
        return PublishResult(
            success=True,
            platform=self.name,
            message="模拟发布成功",
            url="https://example.com/mock/123",
        )


class TestPublishMode:
    """发布模式测试."""

    def test_simulate_mode(self):
        """测试模拟模式."""
        assert PublishMode.SIMULATE.value == "simulate"

    def test_real_mode(self):
        """测试真实模式."""
        assert PublishMode.REAL.value == "real"


class TestPublishResult:
    """发布结果测试."""

    def test_success_result(self):
        """测试成功结果."""
        result = PublishResult(
            success=True,
            platform="test",
            message="发布成功",
            url="https://example.com/1",
        )
        assert result.success is True
        assert result.platform == "test"
        assert "成功" in str(result)

    def test_failure_result(self):
        """测试失败结果."""
        result = PublishResult(
            success=False,
            platform="test",
            message="发布失败",
        )
        assert result.success is False
        assert "失败" in str(result)

    def test_default_published_at(self):
        """测试默认发布时间."""
        result = PublishResult(success=True, platform="test", message="测试")
        assert isinstance(result.published_at, datetime)


class TestPlatformBase:
    """平台基类测试."""

    def setup_method(self):
        """测试前准备."""
        self.platform = MockPlatform()

    def test_platform_initialization(self):
        """测试平台初始化."""
        assert self.platform.name == "mock"
        assert self.platform.max_title_length == 50
        assert self.platform.max_content_length == 1000
        assert self.platform.max_images == 5

    def test_adapt_title_short(self):
        """测试短标题适配."""
        title = "短标题"
        result = self.platform.adapt_title(title)
        assert result == title

    def test_adapt_title_long(self):
        """测试长标题截断."""
        title = "这是一个很长很长很长很长很长很长很长很长很长很长很长的标题，超过50个字符"
        result = self.platform.adapt_title(title)
        assert len(result) <= 50
        assert result.endswith("...")

    def test_adapt_content_short(self):
        """测试短内容适配."""
        content = "短内容"
        result = self.platform.adapt_content(content)
        assert result == content

    def test_adapt_content_long(self):
        """测试长内容截断."""
        content = "x" * 2000
        result = self.platform.adapt_content(content)
        assert len(result) <= 1000

    def test_validate_images_success(self):
        """测试图片验证成功."""
        images = ["img1.jpg", "img2.jpg", "img3.jpg"]
        result = self.platform.validate_images(images)
        assert len(result) == 3

    def test_validate_images_exceed_limit(self):
        """测试图片数量超限."""
        images = ["img1.jpg"] * 10
        with pytest.raises(ValueError, match="超过平台限制"):
            self.platform.validate_images(images)

    def test_simulate_publish(self):
        """测试模拟发布."""
        result = self.platform.publish(
            title="测试标题",
            content="测试内容",
            images=["test.jpg"],
            mode=PublishMode.SIMULATE,
        )
        assert result.success is True
        assert result.platform == "mock"
        assert "模拟发布" in result.message

    def test_real_publish(self):
        """测试真实发布."""
        result = self.platform.publish(
            title="测试标题",
            content="测试内容",
            images=["test.jpg"],
            mode=PublishMode.REAL,
        )
        assert result.success is True
        assert result.url == "https://example.com/mock/123"

    def test_publish_with_image_error(self):
        """测试发布时图片验证失败."""
        result = self.platform.publish(
            title="测试",
            content="内容",
            images=["img.jpg"] * 10,
            mode=PublishMode.REAL,
        )
        assert result.success is False
        assert "超过平台限制" in result.message

    def test_repr(self):
        """测试对象字符串表示."""
        assert "MockPlatform" in repr(self.platform)
        assert "mock" in repr(self.platform)

    def test_title_truncation_with_ellipsis(self):
        """测试标题截断后添加省略号."""
        long_title = "这是一" * 20 + "个很长的标题"
        result = self.platform.adapt_title(long_title)
        assert len(result) <= 50
        assert result.endswith("...")

    def test_title_no_truncation_when_short(self):
        """测试短标题不截断."""
        short_title = "短标题"
        result = self.platform.adapt_title(short_title)
        assert result == short_title
        assert not result.endswith("...")

    def test_content_truncation_preserves_meaning(self):
        """测试内容截断保留完整意思."""
        long_content = "重要段落。\n" + "x" * 2000
        result = self.platform.adapt_content(long_content)
        assert "重要段落" in result
        assert "内容过长" in result or len(result) <= 1000

    def test_image_limit_boundary(self):
        """测试图片数量边界值."""
        # 正好等于限制
        images = ["img.jpg"] * 5
        result = self.platform.validate_images(images)
        assert len(result) == 5

        # 超过限制1张
        images = ["img.jpg"] * 6
        with pytest.raises(ValueError):
            self.platform.validate_images(images)

    def test_simulate_publish_returns_preview_info(self):
        """测试模拟发布返回预览信息."""
        result = self.platform.publish(
            title="测试标题",
            content="测试内容",
            images=["img1.jpg", "img2.jpg"],
            mode=PublishMode.SIMULATE,
        )
        assert result.success is True
        assert result.raw_response is not None
        assert result.raw_response["images_count"] == 2
        assert result.raw_response["content_type"] == "richtext"

    def test_publish_empty_images(self):
        """测试无图片发布."""
        result = self.platform.publish(
            title="标题",
            content="内容",
            images=[],
            mode=PublishMode.SIMULATE,
        )
        assert result.success is True

    def test_publish_none_images(self):
        """测试images为None时发布."""
        result = self.platform.publish(
            title="标题",
            content="内容",
            mode=PublishMode.SIMULATE,
        )
        assert result.success is True
