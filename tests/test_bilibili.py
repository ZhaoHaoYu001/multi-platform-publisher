"""B站平台测试模块."""

import pytest

from src.core.platform_base import PublishMode
from src.platforms.bilibili import BilibiliPlatform


class TestBilibiliPlatform:
    """B站平台测试."""

    def setup_method(self):
        """测试前准备."""
        self.platform = BilibiliPlatform()

    def test_platform_config(self):
        """测试平台配置."""
        assert self.platform.name == "bilibili"
        assert self.platform.max_title_length == 80
        assert self.platform.max_content_length == 15000
        assert self.platform.max_images == 100
        assert self.platform.content_type == "richtext"

    def test_init_with_credentials(self):
        """测试带凭证初始化."""
        platform = BilibiliPlatform(sess_data="test_sess", csrf="test_csrf")
        assert platform.sess_data == "test_sess"
        assert platform.csrf == "test_csrf"

    def test_adapt_title_normal(self):
        """测试正常标题适配."""
        title = "B站专栏标题"
        result = self.platform.adapt_title(title)
        assert result == title

    def test_adapt_title_long(self):
        """测试长标题截断."""
        title = "这是一个很长的B站专栏标题" * 10
        result = self.platform.adapt_title(title)
        assert len(result) <= 80
        assert result.endswith("...")

    def test_adapt_content_heading(self):
        """测试标题转换."""
        markdown = "# 一级标题\n\n## 二级标题"
        result = self.platform.adapt_content(markdown)
        assert "**一级标题**" in result
        assert "**二级标题**" in result

    def test_adapt_content_divider(self):
        """测试分割线转换."""
        markdown = "内容1\n---\n内容2"
        result = self.platform.adapt_content(markdown)
        assert "——————" in result

    def test_validate_images_success(self):
        """测试图片验证成功."""
        images = ["img1.jpg"] * 50
        result = self.platform.validate_images(images)
        assert len(result) == 50

    def test_validate_images_exceed_limit(self):
        """测试图片数量超限."""
        images = ["img.jpg"] * 101
        with pytest.raises(ValueError, match="超过平台限制"):
            self.platform.validate_images(images)

    def test_simulate_publish(self):
        """测试模拟发布."""
        result = self.platform.publish(
            title="测试标题",
            content="# 测试内容\n\n这是测试",
            images=["test.jpg"],
            mode=PublishMode.SIMULATE,
        )
        assert result.success is True
        assert result.platform == "bilibili"
        assert "模拟发布" in result.message

    def test_real_publish(self):
        """测试真实发布（返回API提示）."""
        result = self.platform.publish(
            title="测试标题",
            content="测试内容",
            images=["test.jpg"],
            mode=PublishMode.REAL,
        )
        assert result.success is True
        assert "B站专栏发布需要以下步骤" in result.message

    def test_check_login_no_creds(self):
        """测试无凭证检查登录."""
        result = self.platform.check_login()
        assert result is False

    def test_check_login_with_creds(self):
        """测试有凭证检查登录（待实现）."""
        platform = BilibiliPlatform(sess_data="test")
        result = platform.check_login()
        # TODO: 实现后改为 assert result is True
        assert result is False

    def test_repr(self):
        """测试对象表示."""
        assert "BilibiliPlatform" in repr(self.platform)
        assert "bilibili" in repr(self.platform)
