"""媒体管理器测试模块."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from src.media.image_processor import ImageProcessor
from src.media.media_manager import MediaItem, MediaManager, MediaType
from src.media.video_processor import VideoProcessor


@pytest.fixture
def temp_dir():
    """创建临时目录."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield tmpdir


@pytest.fixture
def workspace_dir(temp_dir):
    """创建工作目录."""
    workspace = os.path.join(temp_dir, "workspace")
    os.makedirs(workspace)
    return workspace


@pytest.fixture
def sample_images(temp_dir):
    """创建示例图片."""
    paths = []
    for i, color in enumerate(["red", "green", "blue"]):
        path = os.path.join(temp_dir, f"image_{i}.jpg")
        img = Image.new("RGB", (800, 600), color=color)
        img.save(path, "JPEG")
        paths.append(path)
    return paths


@pytest.fixture
def manager(workspace_dir):
    """创建媒体管理器实例."""
    return MediaManager(workspace_dir=workspace_dir)


class TestMediaType:
    """媒体类型测试."""

    def test_image_type(self):
        """测试图片类型."""
        assert MediaType.IMAGE.value == "image"

    def test_video_type(self):
        """测试视频类型."""
        assert MediaType.VIDEO.value == "video"


class TestMediaItem:
    """媒体项测试."""

    def test_filename(self, temp_dir):
        """测试获取文件名."""
        path = os.path.join(temp_dir, "test.jpg")
        item = MediaItem(path=path, media_type=MediaType.IMAGE)
        assert item.filename == "test.jpg"

    def test_exists(self, temp_dir):
        """测试文件存在检查."""
        path = os.path.join(temp_dir, "test.jpg")
        # 创建文件
        Image.new("RGB", (100, 100)).save(path, "JPEG")

        item = MediaItem(path=path, media_type=MediaType.IMAGE)
        assert item.exists is True

    def test_not_exists(self):
        """测试文件不存在."""
        item = MediaItem(path="/nonexistent/test.jpg", media_type=MediaType.IMAGE)
        assert item.exists is False


class TestMediaManagerInit:
    """媒体管理器初始化测试."""

    def test_default_init(self, temp_dir):
        """测试默认初始化."""
        os.chdir(temp_dir)
        manager = MediaManager()
        assert os.path.exists(manager.workspace_dir)

    def test_custom_workspace(self, workspace_dir):
        """测试自定义工作目录."""
        manager = MediaManager(workspace_dir=workspace_dir)
        assert manager.workspace_dir == workspace_dir

    def test_initial_state(self, manager):
        """测试初始状态."""
        assert manager.count == 0
        assert manager.images == []
        assert manager.videos == []


class TestAddImage:
    """添加图片测试."""

    def test_add_image(self, manager, sample_images):
        """测试添加图片."""
        item = manager.add_image(sample_images[0], caption="测试图片")
        assert item.media_type == MediaType.IMAGE
        assert item.caption == "测试图片"
        assert item.image_info is not None
        assert manager.count == 1

    def test_add_multiple_images(self, manager, sample_images):
        """测试添加多张图片."""
        for path in sample_images:
            manager.add_image(path)
        assert manager.count == 3
        assert len(manager.images) == 3

    def test_add_image_not_found(self, manager):
        """测试添加不存在的图片."""
        with pytest.raises(FileNotFoundError):
            manager.add_image("nonexistent.jpg")

    def test_add_image_with_order(self, manager, sample_images):
        """测试指定排序添加图片."""
        manager.add_image(sample_images[0], order=2)
        manager.add_image(sample_images[1], order=1)
        manager.add_image(sample_images[2], order=0)

        items = manager.items
        assert items[0].order == 0
        assert items[2].order == 2

    def test_add_image_copy_to_workspace(self, manager, sample_images, workspace_dir):
        """测试复制到工作目录."""
        item = manager.add_image(sample_images[0], copy_to_workspace=True)
        assert workspace_dir in item.path


class TestRemoveAndClear:
    """移除和清空测试."""

    def test_remove_item(self, manager, sample_images):
        """测试移除媒体项."""
        manager.add_image(sample_images[0])
        assert manager.count == 1

        result = manager.remove_item(sample_images[0])
        assert result is True
        assert manager.count == 0

    def test_remove_nonexistent(self, manager):
        """测试移除不存在的项."""
        result = manager.remove_item("nonexistent.jpg")
        assert result is False

    def test_clear(self, manager, sample_images):
        """测试清空所有项."""
        for path in sample_images:
            manager.add_image(path)
        assert manager.count == 3

        manager.clear()
        assert manager.count == 0


class TestReorderAndUpdate:
    """排序和更新测试."""

    def test_reorder(self, manager, sample_images):
        """测试调整排序."""
        manager.add_image(sample_images[0], order=0)
        manager.add_image(sample_images[1], order=1)

        manager.reorder(sample_images[0], new_order=5)
        items = manager.items
        assert items[1].order == 5

    def test_update_caption(self, manager, sample_images):
        """测试更新说明文字."""
        manager.add_image(sample_images[0], caption="原始")
        manager.update_caption(sample_images[0], "更新后")

        item = manager.items[0]
        assert item.caption == "更新后"


class TestProcessForPlatform:
    """平台处理测试."""

    def test_process_for_wechat(self, manager, sample_images):
        """测试微信平台处理."""
        manager.add_image(sample_images[0])
        results = manager.process_for_platform("wechat")

        assert len(results) == 1
        # 处理后的文件应该存在或包含ERROR
        for original, processed in results.items():
            assert os.path.exists(processed) or "ERROR" in processed

    def test_process_for_invalid_platform(self, manager, sample_images):
        """测试无效平台."""
        manager.add_image(sample_images[0])
        with pytest.raises(ValueError, match="不支持的平台"):
            manager.process_for_platform("invalid")

    def test_process_empty(self, manager):
        """测试空列表处理."""
        results = manager.process_for_platform("wechat")
        assert results == {}


class TestSummary:
    """摘要测试."""

    def test_get_summary(self, manager, sample_images):
        """测试获取摘要."""
        for path in sample_images:
            manager.add_image(path)

        summary = manager.get_summary()
        assert "3" in summary  # 3张图片
        assert "图片" in summary

    def test_repr(self, manager, sample_images):
        """测试字符串表示."""
        manager.add_image(sample_images[0])
        repr_str = repr(manager)
        assert "MediaManager" in repr_str
        assert "images=1" in repr_str


class TestLenOperator:
    """长度操作符测试."""

    def test_len_empty(self, manager):
        """测试空管理器长度."""
        assert len(manager) == 0

    def test_len_with_items(self, manager, sample_images):
        """测试有项时的长度."""
        manager.add_image(sample_images[0])
        manager.add_image(sample_images[1])
        assert len(manager) == 2
