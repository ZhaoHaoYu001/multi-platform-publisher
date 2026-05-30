"""图片处理器测试模块."""

import os
import tempfile

import pytest
from PIL import Image

from src.media.image_processor import AspectRatio, ImageInfo, ImageProcessor


@pytest.fixture
def temp_dir():
    """创建临时目录."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_image(temp_dir):
    """创建示例图片."""
    img_path = os.path.join(temp_dir, "test.jpg")
    img = Image.new("RGB", (1920, 1080), color="red")
    img.save(img_path, "JPEG")
    return img_path


@pytest.fixture
def sample_square_image(temp_dir):
    """创建方形示例图片."""
    img_path = os.path.join(temp_dir, "square.jpg")
    img = Image.new("RGB", (1000, 1000), color="blue")
    img.save(img_path, "JPEG")
    return img_path


@pytest.fixture
def processor():
    """创建图片处理器实例."""
    return ImageProcessor()


class TestAspectRatio:
    """比例枚举测试."""

    def test_square(self):
        """测试正方形比例."""
        assert AspectRatio.SQUARE.value == (1, 1)

    def test_landscape(self):
        """测试横版比例."""
        assert AspectRatio.LANDSCAPE.value == (16, 9)

    def test_portrait(self):
        """测试竖版比例."""
        assert AspectRatio.PORTRAIT.value == (3, 4)


class TestImageInfo:
    """图片信息测试."""

    def test_str(self):
        """测试字符串表示."""
        info = ImageInfo(
            width=1920,
            height=1080,
            format="JPEG",
            size=1024 * 1024,
            mode="RGB",
        )
        result = str(info)
        assert "1920x1080" in result
        assert "JPEG" in result
        assert "1.00MB" in result


class TestImageProcessor:
    """图片处理器测试."""

    def test_get_image_info(self, processor, sample_image):
        """测试获取图片信息."""
        info = processor.get_image_info(sample_image)
        assert info.width == 1920
        assert info.height == 1080
        assert info.format == "JPEG"
        assert info.mode == "RGB"

    def test_get_image_info_not_found(self, processor):
        """测试文件不存在."""
        with pytest.raises(FileNotFoundError):
            processor.get_image_info("nonexistent.jpg")

    def test_resize_by_width(self, processor, sample_image, temp_dir):
        """测试按宽度调整."""
        output = os.path.join(temp_dir, "resized.jpg")
        processor.resize_image(sample_image, output, width=800)

        info = processor.get_image_info(output)
        assert info.width == 800
        assert info.height == 450  # 保持16:9比例

    def test_resize_by_height(self, processor, sample_image, temp_dir):
        """测试按高度调整."""
        output = os.path.join(temp_dir, "resized.jpg")
        processor.resize_image(sample_image, output, height=540)

        info = processor.get_image_info(output)
        assert info.height == 540
        assert info.width == 960

    def test_resize_both(self, processor, sample_image, temp_dir):
        """测试同时指定宽高."""
        output = os.path.join(temp_dir, "resized.jpg")
        processor.resize_image(sample_image, output, width=800, height=600)

        info = processor.get_image_info(output)
        assert info.width <= 800
        assert info.height <= 600

    def test_resize_no_params(self, processor, sample_image, temp_dir):
        """测试不指定尺寸抛出异常."""
        output = os.path.join(temp_dir, "resized.jpg")
        with pytest.raises(ValueError, match="至少需要指定一个"):
            processor.resize_image(sample_image, output)

    def test_compress_image(self, processor, sample_image, temp_dir):
        """测试压缩图片."""
        output = os.path.join(temp_dir, "compressed.jpg")
        processor.compress_image(sample_image, output, max_size_mb=0.5)

        info = processor.get_image_info(output)
        assert info.size <= 0.5 * 1024 * 1024

    def test_crop_to_square(self, processor, sample_image, temp_dir):
        """测试裁剪为正方形."""
        output = os.path.join(temp_dir, "square.jpg")
        processor.crop_to_ratio(sample_image, output, AspectRatio.SQUARE)

        info = processor.get_image_info(output)
        assert info.width == info.height

    def test_crop_to_landscape(self, processor, sample_square_image, temp_dir):
        """测试裁剪为横版."""
        output = os.path.join(temp_dir, "landscape.jpg")
        processor.crop_to_ratio(sample_square_image, output, AspectRatio.LANDSCAPE)

        info = processor.get_image_info(output)
        ratio = info.width / info.height
        assert abs(ratio - 16 / 9) < 0.01

    def test_crop_to_portrait(self, processor, sample_square_image, temp_dir):
        """测试裁剪为竖版."""
        output = os.path.join(temp_dir, "portrait.jpg")
        processor.crop_to_ratio(sample_square_image, output, AspectRatio.PORTRAIT)

        info = processor.get_image_info(output)
        ratio = info.width / info.height
        assert abs(ratio - 3 / 4) < 0.01


class TestPlatformRequirements:
    """平台需求测试."""

    def test_prepare_for_wechat(self, processor, sample_square_image, temp_dir):
        """测试微信平台处理."""
        output = os.path.join(temp_dir, "wechat.jpg")
        result = processor.prepare_for_platform(
            sample_square_image, "wechat", output
        )
        assert os.path.exists(result)

        info = processor.get_image_info(result)
        assert info.width >= 640
        assert info.height >= 640

    def test_prepare_for_bilibili(self, processor, sample_image, temp_dir):
        """测试B站平台处理."""
        output = os.path.join(temp_dir, "bilibili.jpg")
        result = processor.prepare_for_platform(
            sample_image, "bilibili", output
        )
        assert os.path.exists(result)

    def test_prepare_for_xiaohongshu(self, processor, sample_square_image, temp_dir):
        """测试小红书平台处理."""
        output = os.path.join(temp_dir, "xiaohongshu.jpg")
        result = processor.prepare_for_platform(
            sample_square_image, "xiaohongshu", output
        )
        assert os.path.exists(result)

        info = processor.get_image_info(result)
        ratio = info.width / info.height
        assert abs(ratio - 3 / 4) < 0.01

    def test_prepare_for_zhihu(self, processor, sample_image, temp_dir):
        """测试知乎平台处理（无固定比例）."""
        output = os.path.join(temp_dir, "zhihu.jpg")
        result = processor.prepare_for_platform(sample_image, "zhihu", output)
        assert os.path.exists(result)

    def test_prepare_for_invalid_platform(self, processor, sample_image, temp_dir):
        """测试不支持的平台."""
        with pytest.raises(ValueError, match="不支持的平台"):
            processor.prepare_for_platform(sample_image, "invalid", "out.jpg")

    def test_prepare_auto_output_path(self, processor, sample_image):
        """测试自动生成输出路径."""
        result = processor.prepare_for_platform(sample_image, "wechat")
        assert "_wechat" in result
        # 清理
        if os.path.exists(result):
            os.remove(result)
