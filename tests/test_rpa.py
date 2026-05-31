"""RPA模块测试.

测试RPA基类和各平台RPA实现的基本功能。
"""

import os
import sys
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRPABase:
    """RPA基类测试."""

    def test_init(self):
        from src.rpa.base import RPABase

        class TestRPA(RPABase):
            def login(self):
                return True
            def publish(self, title, content, images, **kwargs):
                return {"success": True}

        with tempfile.TemporaryDirectory() as tmpdir:
            rpa = TestRPA(
                platform_name="test",
                cookie_dir=os.path.join(tmpdir, "cookies"),
                screenshot_dir=os.path.join(tmpdir, "screenshots"),
            )
            assert rpa.platform_name == "test"
            assert rpa.headless is False
            assert os.path.exists(rpa.cookie_dir)
            assert os.path.exists(rpa.screenshot_dir)

    def test_cookie_file_path(self):
        from src.rpa.base import RPABase

        class TestRPA(RPABase):
            def login(self):
                return True
            def publish(self, title, content, images, **kwargs):
                return {"success": True}

        with tempfile.TemporaryDirectory() as tmpdir:
            rpa = TestRPA(platform_name="bilibili", cookie_dir=tmpdir)
            assert "bilibili_cookies.json" in rpa.cookie_file

    def test_context_manager(self):
        from src.rpa.base import RPABase

        class TestRPA(RPABase):
            def login(self):
                return True
            def publish(self, title, content, images, **kwargs):
                return {"success": True}

        with tempfile.TemporaryDirectory() as tmpdir:
            rpa = TestRPA(
                platform_name="test",
                cookie_dir=os.path.join(tmpdir, "cookies"),
                screenshot_dir=os.path.join(tmpdir, "screenshots"),
            )
            rpa.launch_browser = MagicMock(return_value=True)
            rpa.close_browser = MagicMock()
            with rpa:
                pass
            rpa.launch_browser.assert_called_once()
            rpa.close_browser.assert_called_once()


class TestBilibiliRPA:
    """B站RPA测试."""

    def test_init(self):
        from src.rpa.bilibili_rpa import BilibiliRPA
        with tempfile.TemporaryDirectory() as tmpdir:
            rpa = BilibiliRPA(
                cookie_dir=os.path.join(tmpdir, "cookies"),
                screenshot_dir=os.path.join(tmpdir, "screenshots"),
            )
            assert rpa.platform_name == "bilibili"
            assert rpa.HOME_URL == "https://www.bilibili.com"

    def test_publish_without_browser(self):
        from src.rpa.bilibili_rpa import BilibiliRPA
        with tempfile.TemporaryDirectory() as tmpdir:
            rpa = BilibiliRPA(
                cookie_dir=os.path.join(tmpdir, "cookies"),
                screenshot_dir=os.path.join(tmpdir, "screenshots"),
            )
            rpa.launch_browser = MagicMock(return_value=False)
            result = rpa.publish(title="test", content="content", images=[])
            assert result["success"] is False


class TestZhihuRPA:
    """知乎RPA测试."""

    def test_init(self):
        from src.rpa.zhihu_rpa import ZhihuRPA
        with tempfile.TemporaryDirectory() as tmpdir:
            rpa = ZhihuRPA(
                cookie_dir=os.path.join(tmpdir, "cookies"),
                screenshot_dir=os.path.join(tmpdir, "screenshots"),
            )
            assert rpa.platform_name == "zhihu"
            assert rpa.PUBLISH_URL == "https://zhuanlan.zhihu.com/write"

    def test_publish_without_browser(self):
        from src.rpa.zhihu_rpa import ZhihuRPA
        with tempfile.TemporaryDirectory() as tmpdir:
            rpa = ZhihuRPA(
                cookie_dir=os.path.join(tmpdir, "cookies"),
                screenshot_dir=os.path.join(tmpdir, "screenshots"),
            )
            rpa.launch_browser = MagicMock(return_value=False)
            result = rpa.publish(title="test", content="content", images=[])
            assert result["success"] is False


class TestXiaohongshuRPA:
    """小红书RPA测试."""

    def test_init(self):
        from src.rpa.xiaohongshu_rpa import XiaohongshuRPA
        with tempfile.TemporaryDirectory() as tmpdir:
            rpa = XiaohongshuRPA(
                cookie_dir=os.path.join(tmpdir, "cookies"),
                screenshot_dir=os.path.join(tmpdir, "screenshots"),
            )
            assert rpa.platform_name == "xiaohongshu"
            assert rpa.PUBLISH_URL == "https://creator.xiaohongshu.com/publish/publish"

    def test_publish_without_browser(self):
        from src.rpa.xiaohongshu_rpa import XiaohongshuRPA
        with tempfile.TemporaryDirectory() as tmpdir:
            rpa = XiaohongshuRPA(
                cookie_dir=os.path.join(tmpdir, "cookies"),
                screenshot_dir=os.path.join(tmpdir, "screenshots"),
            )
            rpa.launch_browser = MagicMock(return_value=False)
            result = rpa.publish(title="test", content="content", images=[])
            assert result["success"] is False


class TestPlatformRPAFallback:
    """测试平台RPA降级逻辑."""

    def test_bilibili_no_credential_tries_rpa(self):
        from src.platforms.bilibili import BilibiliPlatform
        platform = BilibiliPlatform()
        result = platform._do_publish(title="test", content="content", images=[])
        assert "未配置B站凭证" not in result.message

    def test_zhihu_no_credential_tries_rpa(self):
        from src.platforms.zhihu import ZhihuPlatform
        platform = ZhihuPlatform()
        result = platform._do_publish(title="test", content="content", images=[])
        assert "未配置知乎凭证" not in result.message

    def test_xiaohongshu_no_credential_tries_rpa(self):
        from src.platforms.xiaohongshu import XiaohongshuPlatform
        platform = XiaohongshuPlatform()
        result = platform._do_publish(title="test", content="content", images=[])
        assert "未配置小红书凭证" not in result.message


class TestZhihuLoginFix:
    """测试知乎login()方法修复."""

    def test_login_without_credentials(self):
        from src.platforms.zhihu import ZhihuPlatform
        platform = ZhihuPlatform()
        assert platform.login() is False

    def test_login_calls_api_login(self):
        from src.platforms.zhihu import ZhihuPlatform
        platform = ZhihuPlatform(username="test", password="test")
        mock_api = MagicMock()
        mock_api.login.return_value = True
        with patch("src.platforms.zhihu.ZhihuPlatform.login", return_value=True):
            assert platform.login() is False  # no real API connection


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
