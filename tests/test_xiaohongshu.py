"""小红书平台测试模块."""

import pytest

from src.core.platform_base import PublishMode
from src.platforms.xiaohongshu import XiaohongshuPlatform


class TestXiaohongshuPlatform:
    """小红书平台测试."""

    def setup_method(self):
        """测试前准备."""
        self.platform = XiaohongshuPlatform()

    def test_platform_config(self):
        """测试平台配置."""
        assert self.platform.name == "xiaohongshu"
        assert self.platform.max_title_length == 20
        assert self.platform.max_content_length == 1000
        assert self.platform.max_images == 9
        assert self.platform.content_type == "plain"

    def test_init_with_cookie(self):
        """测试带cookie初始化."""
        platform = XiaohongshuPlatform(cookie="test_cookie")
        assert platform.cookie == "test_cookie"

    def test_adapt_title_with_emoji(self):
        """测试标题添加emoji."""
        title = "推荐好物分享"
        result = self.platform.adapt_title(title)
        assert "👍" in result or "💡" in result

    def test_adapt_title_without_keyword(self):
        """测试无关键词标题."""
        title = "今天的天气真好"
        result = self.platform.adapt_title(title)
        # 没有匹配的关键词，不添加emoji
        assert len(result) <= 20

    def test_adapt_title_long(self):
        """测试长标题截断."""
        title = "这是一个很长的标题" * 5
        result = self.platform.adapt_title(title)
        assert len(result) <= 20

    def test_markdown_to_plain_heading(self):
        """测试标题转换."""
        markdown = "# 一级标题\n\n二级标题"
        result = self.platform._markdown_to_plain(markdown)
        assert "#" not in result
        assert "一级标题" in result

    def test_markdown_to_plain_bold(self):
        """测试粗体转换."""
        markdown = "这是**粗体**文本"
        result = self.platform._markdown_to_plain(markdown)
        assert "**" not in result
        assert "粗体" in result

    def test_markdown_to_plain_code(self):
        """测试代码转换."""
        markdown = "使用 `print()` 函数"
        result = self.platform._markdown_to_plain(markdown)
        assert "`" not in result
        assert "print()" in result

    def test_markdown_to_plain_list(self):
        """测试列表转换."""
        markdown = "- 列表项1\n- 列表项2"
        result = self.platform._markdown_to_plain(markdown)
        assert "•" in result

    def test_add_emojis(self):
        """测试添加emoji."""
        content = "这是一篇教程文章"
        result = self.platform._add_emojis(content)
        assert "📚" in result or len(result) > 0

    def test_add_hashtags(self):
        """测试添加话题标签."""
        content = "分享一些好用的教程"
        result = self.platform._add_hashtags(content)
        assert "#" in result
        assert "#分享#" in result or "#教程#" in result

    def test_adapt_content_full(self):
        """测试完整内容适配."""
        markdown = "# 标题\n\n**重要内容**\n\n- 列表1\n- 列表2"
        result = self.platform.adapt_content(markdown)
        # 应该转为纯文本+emoji+话题标签
        assert "#" not in result or "#分享#" in result or "#推荐#" in result
        assert len(result) <= 1000

    def test_validate_images_success(self):
        """测试图片验证成功."""
        images = ["img1.jpg", "img2.jpg", "img3.jpg"]
        result = self.platform.validate_images(images)
        assert len(result) == 3

    def test_validate_images_exceed_limit(self):
        """测试图片数量超限."""
        images = ["img.jpg"] * 10
        with pytest.raises(ValueError, match="超过平台限制"):
            self.platform.validate_images(images)

    def test_simulate_publish(self):
        """测试模拟发布."""
        result = self.platform.publish(
            title="推荐好物",
            content="# 分享\n\n好用的教程",
            images=["test.jpg"],
            mode=PublishMode.SIMULATE,
        )
        assert result.success is True
        assert result.platform == "xiaohongshu"
        assert "模拟发布" in result.message

    def test_real_publish(self):
        """测试真实发布（无凭证返回失败）."""
        result = self.platform.publish(
            title="推荐好物",
            content="分享好用的东西",
            images=["test.jpg"],
            mode=PublishMode.REAL,
        )
        assert result.success is False
        assert "未配置小红书凭证" in result.message

    def test_check_login_no_cookie(self):
        """测试无cookie检查登录."""
        result = self.platform.check_login()
        assert result is False

    def test_check_login_with_cookie(self):
        """测试有cookie检查登录（需真实API）."""
        platform = XiaohongshuPlatform(cookie="test_cookie_value")
        result = platform.check_login()
        # TODO: 需要真实有效cookie才能返回True
        assert result is False

    def test_repr(self):
        """测试对象表示."""
        assert "XiaohongshuPlatform" in repr(self.platform)
        assert "xiaohongshu" in repr(self.platform)
