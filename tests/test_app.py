"""主程序测试模块."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app import App
from publish import init_platform_manager, load_content, load_images


class TestLoadContent:
    """加载内容测试."""

    def test_load_from_string(self):
        """测试从字符串加载."""
        content = load_content("直接内容", "")
        assert content == "直接内容"

    def test_load_from_file(self, tmp_path):
        """测试从文件加载."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# 文件内容\n\n测试", encoding="utf-8")

        content = load_content("", str(test_file))
        assert "文件内容" in content

    def test_load_file_priority(self, tmp_path):
        """测试文件优先."""
        test_file = tmp_path / "test.md"
        test_file.write_text("文件内容", encoding="utf-8")

        content = load_content("直接内容", str(test_file))
        assert content == "文件内容"

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件."""
        with pytest.raises(SystemExit):
            load_content("", "nonexistent.md")


class TestLoadImages:
    """加载图片测试."""

    def test_load_existing_images(self, tmp_path):
        """测试加载存在的图片."""
        img1 = tmp_path / "img1.jpg"
        img2 = tmp_path / "img2.jpg"
        img1.write_text("fake")
        img2.write_text("fake")

        images = load_images([str(img1), str(img2)])
        assert len(images) == 2

    def test_load_with_nonexistent(self, tmp_path):
        """测试加载包含不存在的图片."""
        img1 = tmp_path / "img1.jpg"
        img1.write_text("fake")

        images = load_images([str(img1), "nonexistent.jpg"])
        assert len(images) == 1

    def test_load_empty_list(self):
        """测试加载空列表."""
        images = load_images([])
        assert images == []


class TestInitPlatformManager:
    """平台管理器初始化测试."""

    @patch.dict(os.environ, {}, clear=True)
    def test_init_default_platforms(self):
        """测试默认平台."""
        manager = init_platform_manager(["wechat", "zhihu", "bilibili", "xiaohongshu"])
        assert manager.count == 4

    def test_init_specific_platforms(self):
        """测试指定平台."""
        manager = init_platform_manager(["wechat", "zhihu"])
        assert manager.count == 2
        assert "wechat" in manager.platforms
        assert "zhihu" in manager.platforms

    def test_init_unknown_platform(self):
        """测试未知平台."""
        manager = init_platform_manager(["unknown"])
        assert manager.count == 0


class TestApp:
    """应用程序测试."""

    @patch.dict(os.environ, {}, clear=True)
    def test_app_init(self):
        """测试应用程序初始化."""
        app = App()
        assert app.current_title == ""
        assert app.current_content == ""
        assert app.current_tags == []
        assert app.platform_manager is not None
