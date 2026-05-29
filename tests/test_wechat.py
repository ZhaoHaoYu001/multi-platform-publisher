"""微信公众号平台测试模块."""

import pytest

from src.core.platform_base import PublishMode
from src.platforms.wechat import WechatPlatform


class TestWechatPlatform:
    """微信公众号平台测试."""

    def setup_method(self):
        """测试前准备."""
        self.platform = WechatPlatform()

    def test_platform_config(self):
        """测试平台配置."""
        assert self.platform.name == "wechat"
        assert self.platform.max_title_length == 64
        assert self.platform.max_images == 10
        assert self.platform.content_type == "richtext"

    def test_init_with_credentials(self):
        """测试带凭证初始化."""
        platform = WechatPlatform(app_id="test_id", app_secret="test_secret")
        assert platform.app_id == "test_id"
        assert platform.app_secret == "test_secret"

    def test_adapt_title_normal(self):
        """测试正常标题适配."""
        title = "短标题"
        result = self.platform.adapt_title(title)
        assert result == title

    def test_adapt_title_long(self):
        """测试长标题截断."""
        title = "这是一个很长的标题" * 10
        result = self.platform.adapt_title(title)
        assert len(result) <= 64
        assert result.endswith("...")

    def test_adapt_content_markdown_to_richtext(self):
        """测试Markdown转富文本."""
        markdown = "# 标题\n\n**粗体**和*斜体*"
        result = self.platform.adapt_content(markdown)
        assert "<h1>标题</h1>" in result
        assert "<strong>粗体</strong>" in result
        assert "<em>斜体</em>" in result

    def test_adapt_content_code(self):
        """测试代码块转换."""
        markdown = "使用 `print()` 函数"
        result = self.platform.adapt_content(markdown)
        assert "<code>print()</code>" in result

    def test_adapt_content_blockquote(self):
        """测试引用转换."""
        markdown = "> 这是引用内容"
        result = self.platform.adapt_content(markdown)
        assert "<blockquote>" in result

    def test_validate_images_success(self):
        """测试图片验证成功."""
        images = ["img1.jpg", "img2.jpg"]
        result = self.platform.validate_images(images)
        assert len(result) == 2

    def test_validate_images_exceed_limit(self):
        """测试图片数量超限."""
        images = ["img.jpg"] * 15
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
        assert result.platform == "wechat"
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
        assert "微信公众号发布需要以下步骤" in result.message
        assert "access_token" in result.message

    def test_get_access_token_no_creds(self):
        """测试无凭证获取token."""
        token = self.platform.get_access_token()
        assert token is None

    def test_get_access_token_with_creds(self):
        """测试有凭证获取token（待实现）."""
        platform = WechatPlatform(app_id="id", app_secret="secret")
        token = platform.get_access_token()
        # TODO: 实现后改为 assert token is not None
        assert token is None

    def test_repr(self):
        """测试对象表示."""
        assert "WechatPlatform" in repr(self.platform)
        assert "wechat" in repr(self.platform)
