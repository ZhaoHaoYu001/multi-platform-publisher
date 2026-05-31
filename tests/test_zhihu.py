"""知乎平台测试模块."""

import pytest

from src.core.platform_base import PublishMode
from src.platforms.zhihu import ZhihuPlatform


class TestZhihuPlatform:
    """知乎平台测试."""

    def setup_method(self):
        """测试前准备."""
        self.platform = ZhihuPlatform()

    def test_platform_config(self):
        """测试平台配置."""
        assert self.platform.name == "zhihu"
        assert self.platform.max_title_length == 60
        assert self.platform.max_content_length == 20000
        assert self.platform.max_images == 30
        assert self.platform.content_type == "markdown"

    def test_init_with_credentials(self):
        """测试带凭证初始化."""
        platform = ZhihuPlatform(username="test", password="pass")
        assert platform.username == "test"
        assert platform.password == "pass"

    def test_adapt_title_normal(self):
        """测试正常标题适配."""
        title = "知乎文章标题"
        result = self.platform.adapt_title(title)
        assert result == title

    def test_adapt_title_long(self):
        """测试长标题截断."""
        title = "这是一个很长的知乎文章标题" * 10
        result = self.platform.adapt_title(title)
        assert len(result) <= 60
        assert result.endswith("...")

    def test_adapt_content_markdown(self):
        """测试Markdown内容适配."""
        markdown = "# 标题\n\n内容"
        result = self.platform.adapt_content(markdown)
        assert result == markdown

    def test_adapt_content_code_block(self):
        """测试代码块语言标注."""
        markdown = "```\nprint('hello')\n```"
        result = self.platform.adapt_content(markdown)
        assert "```text\n" in result

    def test_validate_images_success(self):
        """测试图片验证成功."""
        images = ["img1.jpg"] * 20
        result = self.platform.validate_images(images)
        assert len(result) == 20

    def test_validate_images_exceed_limit(self):
        """测试图片数量超限."""
        images = ["img.jpg"] * 35
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
        assert result.platform == "zhihu"
        assert "模拟发布" in result.message

    def test_real_publish(self):
        """测试真实发布（无凭证回退到RPA）."""
        result = self.platform.publish(
            title="测试标题",
            content="测试内容",
            images=["test.jpg"],
            mode=PublishMode.REAL,
        )
        assert result.success is False
        # 无API凭证时回退到RPA，RPA可能因浏览器未安装而报错
        assert "未配置知乎凭证" in result.message or "RPA" in result.message

    def test_check_login_no_creds(self):
        """测试无凭证登录."""
        result = self.platform.check_login()
        assert result is False

    def test_check_login_with_creds(self):
        """测试有凭证登录（需真实API）."""
        platform = ZhihuPlatform(username="user", password="pass")
        result = platform.check_login()
        # TODO: 需要真实有效凭证才能返回True
        assert result is False

    def test_repr(self):
        """测试对象表示."""
        assert "ZhihuPlatform" in repr(self.platform)
        assert "zhihu" in repr(self.platform)
