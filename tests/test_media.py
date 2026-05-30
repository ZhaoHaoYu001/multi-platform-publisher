"""媒体处理综合测试模块.

本模块包含图片裁剪、压缩等功能的详细测试。
"""

import os
import tempfile

import pytest
from PIL import Image

from src.media.image_processor import AspectRatio, ImageProcessor


@pytest.fixture
def temp_dir():
    """创建临时目录."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def processor():
    """创建图片处理器实例."""
    return ImageProcessor()


@pytest.fixture
def landscape_image(temp_dir):
    """创建横版图片 (16:9)."""
    path = os.path.join(temp_dir, "landscape.jpg")
    img = Image.new("RGB", (1920, 1080), color="red")
    img.save(path, "JPEG", quality=95)
    return path


@pytest.fixture
def portrait_image(temp_dir):
    """创建竖版图片 (3:4)."""
    path = os.path.join(temp_dir, "portrait.jpg")
    img = Image.new("RGB", (750, 1000), color="blue")
    img.save(path, "JPEG", quality=95)
    return path


@pytest.fixture
def square_image(temp_dir):
    """创建正方形图片."""
    path = os.path.join(temp_dir, "square.jpg")
    img = Image.new("RGB", (1000, 1000), color="green")
    img.save(path, "JPEG", quality=95)
    return path


@pytest.fixture
def large_image(temp_dir):
    """创建大尺寸图片用于压缩测试."""
    path = os.path.join(temp_dir, "large.jpg")
    img = Image.new("RGB", (4000, 3000), color="yellow")
    img.save(path, "JPEG", quality=100)
    return path


class TestImageCropping:
    """图片裁剪测试."""

    def test_crop_to_square_from_landscape(self, processor, landscape_image, temp_dir):
        """测试从横版裁剪为正方形."""
        output = os.path.join(temp_dir, "square.jpg")
        processor.crop_to_ratio(landscape_image, output, AspectRatio.SQUARE)

        info = processor.get_image_info(output)
        assert info.width == info.height
        # 应该裁剪宽度
        assert info.width == 1080
        assert info.height == 1080

    def test_crop_to_square_from_portrait(self, processor, portrait_image, temp_dir):
        """测试从竖版裁剪为正方形."""
        output = os.path.join(temp_dir, "square.jpg")
        processor.crop_to_ratio(portrait_image, output, AspectRatio.SQUARE)

        info = processor.get_image_info(output)
        assert info.width == info.height
        # 应该裁剪高度
        assert info.width == 750
        assert info.height == 750

    def test_crop_to_landscape_from_square(self, processor, square_image, temp_dir):
        """测试从正方形裁剪为横版."""
        output = os.path.join(temp_dir, "landscape.jpg")
        processor.crop_to_ratio(square_image, output, AspectRatio.LANDSCAPE)

        info = processor.get_image_info(output)
        ratio = info.width / info.height
        expected_ratio = 16 / 9
        assert abs(ratio - expected_ratio) < 0.01

    def test_crop_to_portrait_from_landscape(self, processor, landscape_image, temp_dir):
        """测试从横版裁剪为竖版."""
        output = os.path.join(temp_dir, "portrait.jpg")
        processor.crop_to_ratio(landscape_image, output, AspectRatio.PORTRAIT)

        info = processor.get_image_info(output)
        ratio = info.width / info.height
        expected_ratio = 3 / 4
        assert abs(ratio - expected_ratio) < 0.01

    def test_crop_preserves_quality(self, processor, landscape_image, temp_dir):
        """测试裁剪保持质量."""
        output = os.path.join(temp_dir, "cropped.jpg")
        processor.crop_to_ratio(landscape_image, output, AspectRatio.SQUARE)

        # 裁剪后应该是JPEG格式
        info = processor.get_image_info(output)
        assert info.format == "JPEG"

    def test_crop_center_alignment(self, processor, temp_dir):
        """测试居中裁剪."""
        # 创建一个有明显中心特征的图片
        path = os.path.join(temp_dir, "centered.png")
        img = Image.new("RGB", (200, 100), color="white")
        # 在中心画一个红点
        img.putpixel((100, 50), (255, 0, 0))
        img.save(path)

        output = os.path.join(temp_dir, "centered_crop.jpg")
        processor.crop_to_ratio(path, output, AspectRatio.SQUARE)

        info = processor.get_image_info(output)
        assert info.width == info.height == 100


class TestImageCompression:
    """图片压缩测试."""

    def test_compress_to_target_size(self, processor, large_image, temp_dir):
        """测试压缩到目标大小."""
        output = os.path.join(temp_dir, "compressed.jpg")
        processor.compress_image(large_image, output, max_size_mb=0.5)

        info = processor.get_image_info(output)
        assert info.size <= 0.5 * 1024 * 1024

    def test_compress_maintains_dimensions(self, processor, large_image, temp_dir):
        """测试压缩保持尺寸."""
        original_info = processor.get_image_info(large_image)
        output = os.path.join(temp_dir, "compressed.jpg")
        processor.compress_image(large_image, output, max_size_mb=1.0)

        compressed_info = processor.get_image_info(output)
        assert compressed_info.width == original_info.width
        assert compressed_info.height == original_info.height

    def test_compress_quality_degradation(self, processor, large_image, temp_dir):
        """测试压缩导致质量降低."""
        output = os.path.join(temp_dir, "compressed.jpg")
        processor.compress_image(large_image, output, max_size_mb=0.1)

        # 文件应该变小
        original_size = os.path.getsize(large_image)
        compressed_size = os.path.getsize(output)
        assert compressed_size < original_size

    def test_compress_already_small_image(self, processor, temp_dir):
        """测试压缩已经很小的图片."""
        # 创建一个小图片
        small_path = os.path.join(temp_dir, "small.jpg")
        img = Image.new("RGB", (100, 100), color="white")
        img.save(small_path, "JPEG", quality=50)

        output = os.path.join(temp_dir, "small_compressed.jpg")
        processor.compress_image(small_path, output, max_size_mb=1.0)

        # 应该正常保存
        assert os.path.exists(output)

    def test_compress_rgba_to_jpeg(self, processor, temp_dir):
        """测试RGBA图片压缩为JPEG."""
        rgba_path = os.path.join(temp_dir, "rgba.png")
        img = Image.new("RGBA", (500, 500), color=(255, 0, 0, 128))
        img.save(rgba_path)

        output = os.path.join(temp_dir, "compressed.jpg")
        processor.compress_image(rgba_path, output, max_size_mb=0.5)

        # 应该成功转换
        info = processor.get_image_info(output)
        assert info.format == "JPEG"
        assert info.mode == "RGB"

    def test_compress_with_custom_quality(self, processor, large_image, temp_dir):
        """测试自定义质量压缩."""
        output_high = os.path.join(temp_dir, "high_quality.jpg")
        output_low = os.path.join(temp_dir, "low_quality.jpg")

        processor.compress_image(large_image, output_high, quality=95)
        processor.compress_image(large_image, output_low, quality=30)

        # 低质量应该更小
        high_size = os.path.getsize(output_high)
        low_size = os.path.getsize(output_low)
        assert low_size <= high_size


class TestImageResize:
    """图片调整尺寸测试."""

    def test_resize_maintains_aspect_ratio(self, processor, landscape_image, temp_dir):
        """测试调整尺寸保持比例."""
        output = os.path.join(temp_dir, "resized.jpg")
        processor.resize_image(landscape_image, output, width=960)

        info = processor.get_image_info(output)
        assert info.width == 960
        assert info.height == 540  # 16:9

    def test_resize_both_dimensions(self, processor, landscape_image, temp_dir):
        """测试同时指定宽高."""
        output = os.path.join(temp_dir, "resized.jpg")
        processor.resize_image(
            landscape_image, output, width=800, height=600, keep_ratio=True
        )

        info = processor.get_image_info(output)
        # 应该适应800x600的框
        assert info.width <= 800
        assert info.height <= 600

    def test_resize_upscale(self, processor, square_image, temp_dir):
        """测试放大图片."""
        output = os.path.join(temp_dir, "upscaled.jpg")
        processor.resize_image(square_image, output, width=2000)

        info = processor.get_image_info(output)
        assert info.width == 2000
        assert info.height == 2000


class TestPlatformIntegration:
    """平台集成测试."""

    def test_wechat_square_processing(self, processor, landscape_image, temp_dir):
        """测试微信平台处理（正方形）."""
        output = os.path.join(temp_dir, "wechat.jpg")
        processor.prepare_for_platform(landscape_image, "wechat", output)

        info = processor.get_image_info(output)
        assert info.width >= 640
        assert info.height >= 640

    def test_bilibili_landscape_processing(self, processor, square_image, temp_dir):
        """测试B站平台处理（横版）."""
        output = os.path.join(temp_dir, "bilibili.jpg")
        processor.prepare_for_platform(square_image, "bilibili", output)

        info = processor.get_image_info(output)
        ratio = info.width / info.height
        assert abs(ratio - 16 / 9) < 0.1

    def test_xiaohongshu_portrait_processing(self, processor, landscape_image, temp_dir):
        """测试小红书平台处理（竖版）."""
        output = os.path.join(temp_dir, "xiaohongshu.jpg")
        processor.prepare_for_platform(landscape_image, "xiaohongshu", output)

        info = processor.get_image_info(output)
        ratio = info.width / info.height
        assert abs(ratio - 3 / 4) < 0.1
