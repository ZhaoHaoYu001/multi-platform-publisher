"""API模块测试模块."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.api.bilibili_api import BilibiliAPI
from src.api.wechat_api import WechatAPI


class TestWechatAPI:
    """微信API测试."""

    def test_init(self):
        """测试初始化."""
        api = WechatAPI(app_id="test_id", app_secret="test_secret")
        assert api.app_id == "test_id"
        assert api.app_secret == "test_secret"

    @patch("requests.get")
    def test_get_access_token_success(self, mock_get):
        """测试成功获取token."""
        mock_get.return_value.json.return_value = {
            "access_token": "test_token",
            "expires_in": 7200,
        }

        api = WechatAPI(app_id="id", app_secret="secret")
        token = api.get_access_token()
        assert token == "test_token"

    @patch("requests.get")
    def test_get_access_token_failure(self, mock_get):
        """测试获取token失败."""
        mock_get.return_value.json.return_value = {
            "errcode": 40013,
            "errmsg": "invalid appid",
        }

        api = WechatAPI(app_id="invalid", app_secret="secret")
        with pytest.raises(ValueError, match="获取access_token失败"):
            api.get_access_token()

    @patch("requests.get")
    def test_upload_material_not_found(self, mock_get):
        """测试上传不存在的文件."""
        api = WechatAPI(app_id="id", app_secret="secret")
        with pytest.raises(FileNotFoundError):
            api.upload_material("nonexistent.jpg")

    def test_is_token_valid_no_token(self):
        """测试无token时的有效性检查."""
        api = WechatAPI(app_id="id", app_secret="secret")
        assert api._is_token_valid() is False


class TestBilibiliAPI:
    """B站API测试."""

    def test_init(self):
        """测试初始化."""
        api = BilibiliAPI(sess_data="test_sess", csrf="test_csrf")
        assert api.sess_data == "test_sess"
        assert api.csrf == "test_csrf"

    @patch("requests.Session.get")
    def test_check_login_success(self, mock_get):
        """测试登录成功."""
        mock_get.return_value.json.return_value = {
            "code": 0,
            "data": {"isLogin": True},
        }

        api = BilibiliAPI(sess_data="valid_sess")
        assert api.check_login() is True

    @patch("requests.Session.get")
    def test_check_login_failure(self, mock_get):
        """测试登录失败."""
        mock_get.return_value.json.return_value = {
            "code": -1,
            "data": {"isLogin": False},
        }

        api = BilibiliAPI(sess_data="invalid_sess")
        assert api.check_login() is False

    def test_markdown_to_bbcode_heading(self):
        """测试标题转换."""
        api = BilibiliAPI()
        markdown = "# 一级标题\n\n## 二级标题"
        bbcode = api.markdown_to_bbcode(markdown)
        assert "[h1]一级标题[/h1]" in bbcode
        assert "[h2]二级标题[/h2]" in bbcode

    def test_markdown_to_bbcode_bold(self):
        """测试粗体转换."""
        api = BilibiliAPI()
        markdown = "这是**粗体**文本"
        bbcode = api.markdown_to_bbcode(markdown)
        assert "[b]粗体[/b]" in bbcode

    def test_markdown_to_bbcode_italic(self):
        """测试斜体转换."""
        api = BilibiliAPI()
        markdown = "这是*斜体*文本"
        bbcode = api.markdown_to_bbcode(markdown)
        assert "[i]斜体[/i]" in bbcode

    def test_markdown_to_bbcode_code(self):
        """测试代码块转换."""
        api = BilibiliAPI()
        markdown = "```python\nprint('hello')\n```"
        bbcode = api.markdown_to_bbcode(markdown)
        assert "[code]" in bbcode
        assert "[/code]" in bbcode

    def test_markdown_to_bbcode_link(self):
        """测试链接转换."""
        api = BilibiliAPI()
        markdown = "[点击这里](https://example.com)"
        bbcode = api.markdown_to_bbcode(markdown)
        assert "[url=https://example.com]点击这里[/url]" in bbcode

    def test_markdown_to_bbcode_image(self):
        """测试图片转换."""
        api = BilibiliAPI()
        markdown = "![图片](image.jpg)"
        bbcode = api.markdown_to_bbcode(markdown)
        assert "[img]image.jpg[/img]" in bbcode

    def test_markdown_to_bbcode_quote(self):
        """测试引用转换."""
        api = BilibiliAPI()
        markdown = "> 这是引用"
        bbcode = api.markdown_to_bbcode(markdown)
        assert "[quote]这是引用[/quote]" in bbcode

    def test_markdown_to_bbcode_strikethrough(self):
        """测试删除线转换."""
        api = BilibiliAPI()
        markdown = "~~删除的内容~~"
        bbcode = api.markdown_to_bbcode(markdown)
        assert "[s]删除的内容[/s]" in bbcode

    def test_markdown_to_bbcode_hr(self):
        """测试分割线转换."""
        api = BilibiliAPI()
        markdown = "内容1\n---\n内容2"
        bbcode = api.markdown_to_bbcode(markdown)
        assert "[hr]" in bbcode
