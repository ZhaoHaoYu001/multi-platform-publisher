"""图片处理器模块.

本模块提供了图片的获取信息、调整尺寸、压缩、裁剪和平台适配功能。
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from PIL import Image


class AspectRatio(Enum):
    """图片比例枚举."""

    SQUARE = (1, 1)  # 正方形
    LANDSCAPE = (16, 9)  # 横版
    PORTRAIT = (3, 4)  # 竖版


@dataclass
class ImageInfo:
    """图片信息数据类.

    Attributes:
        width: 图片宽度（像素）
        height: 图片高度（像素）
        format: 图片格式（JPEG/PNG等）
        size: 文件大小（字节）
        mode: 颜色模式（RGB/RGBA等）
    """

    width: int
    height: int
    format: str
    size: int
    mode: str

    def __str__(self) -> str:
        """返回图片信息的字符串表示."""
        size_mb = self.size / (1024 * 1024)
        return (
            f"{self.width}x{self.height} {self.format} "
            f"{size_mb:.2f}MB {self.mode}"
        )


# 各平台图片要求
PLATFORM_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "wechat": {
        "ratio": AspectRatio.SQUARE,
        "min_size": 640,
        "max_size_bytes": 2 * 1024 * 1024,  # 2MB
        "format": "JPEG",
    },
    "bilibili": {
        "ratio": AspectRatio.LANDSCAPE,
        "min_size": 800,
        "max_size_bytes": 5 * 1024 * 1024,  # 5MB
        "format": "JPEG",
    },
    "xiaohongshu": {
        "ratio": AspectRatio.PORTRAIT,
        "min_size": 1080,
        "max_size_bytes": 1 * 1024 * 1024,  # 1MB
        "format": "JPEG",
    },
    "zhihu": {
        "ratio": None,  # 知乎无固定比例
        "min_size": 0,
        "max_size_bytes": 10 * 1024 * 1024,  # 10MB
        "format": "JPEG",
    },
}


class ImageProcessor:
    """图片处理器，提供图片处理的各种功能.

    使用示例:
        processor = ImageProcessor()

        # 获取图片信息
        info = processor.get_image_info("image.jpg")
        print(info)

        # 调整尺寸
        processor.resize_image("input.jpg", "output.jpg", width=800)

        # 压缩图片
        processor.compress_image("input.jpg", "output.jpg", max_size_mb=1)

        # 为平台处理
        output = processor.prepare_for_platform("input.jpg", "wechat")
    """

    def get_image_info(self, image_path: str) -> ImageInfo:
        """获取图片信息.

        Args:
            image_path: 图片文件路径

        Returns:
            ImageInfo: 图片信息

        Raises:
            FileNotFoundError: 文件不存在时抛出
            ValueError: 无法识别的图片格式时抛出
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        try:
            with Image.open(image_path) as img:
                file_size = os.path.getsize(image_path)
                return ImageInfo(
                    width=img.width,
                    height=img.height,
                    format=img.format or "UNKNOWN",
                    size=file_size,
                    mode=img.mode,
                )
        except Exception as e:
            raise ValueError(f"无法识别图片格式: {e}")

    def resize_image(
        self,
        input_path: str,
        output_path: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        keep_ratio: bool = True,
    ) -> str:
        """调整图片尺寸.

        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            width: 目标宽度（像素），None则按高度等比缩放
            height: 目标高度（像素），None则按宽度等比缩放
            keep_ratio: 是否保持宽高比

        Returns:
            输出文件路径

        Raises:
            ValueError: 参数错误时抛出
        """
        if width is None and height is None:
            raise ValueError("width和height至少需要指定一个")

        with Image.open(input_path) as img:
            if keep_ratio:
                if width and height:
                    # 计算保持比例的尺寸
                    ratio = min(width / img.width, height / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                elif width:
                    ratio = width / img.width
                    new_size = (width, int(img.height * ratio))
                else:
                    ratio = height / img.height  # type: ignore
                    new_size = (int(img.width * ratio), height)  # type: ignore
            else:
                new_size = (
                    width or img.width,
                    height or img.height,
                )

            resized = img.resize(new_size, Image.Resampling.LANCZOS)

            # 保持原始格式
            fmt = img.format or "JPEG"
            if fmt == "JPEG" and resized.mode == "RGBA":
                resized = resized.convert("RGB")

            resized.save(output_path, format=fmt, quality=95)

        return output_path

    def compress_image(
        self,
        input_path: str,
        output_path: str,
        max_size_mb: float = 2.0,
        quality: int = 85,
    ) -> str:
        """压缩图片到指定大小.

        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            max_size_mb: 最大文件大小（MB）
            quality: 初始质量（1-100）

        Returns:
            输出文件路径
        """
        max_size_bytes = int(max_size_mb * 1024 * 1024)

        with Image.open(input_path) as img:
            # 如果是RGBA且保存为JPEG，需要转换
            save_format = "JPEG"
            if img.format == "PNG":
                save_format = "PNG"

            current_quality = quality

            while current_quality > 10:
                # 保存到内存检查大小
                from io import BytesIO

                buffer = BytesIO()

                if save_format == "JPEG":
                    if img.mode == "RGBA":
                        img_to_save = img.convert("RGB")
                    else:
                        img_to_save = img
                    img_to_save.save(buffer, format="JPEG", quality=current_quality)
                else:
                    img.save(buffer, format="PNG", optimize=True)

                if buffer.tell() <= max_size_bytes:
                    # 写入文件
                    with open(output_path, "wb") as f:
                        f.write(buffer.getvalue())
                    return output_path

                current_quality -= 10

            # 最低质量仍超限，保存最小版本
            if save_format == "JPEG":
                img_to_save = img.convert("RGB") if img.mode == "RGBA" else img
                img_to_save.save(output_path, format="JPEG", quality=10)
            else:
                img.save(output_path, format="PNG", optimize=True)

        return output_path

    def crop_to_ratio(
        self,
        input_path: str,
        output_path: str,
        ratio: AspectRatio,
    ) -> str:
        """按比例裁剪图片（从中心裁剪）.

        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            ratio: 目标比例

        Returns:
            输出文件路径
        """
        ratio_w, ratio_h = ratio.value

        with Image.open(input_path) as img:
            img_w, img_h = img.size
            target_ratio = ratio_w / ratio_h
            current_ratio = img_w / img_h

            if current_ratio > target_ratio:
                # 图片太宽，裁剪宽度
                new_width = int(img_h * target_ratio)
                left = (img_w - new_width) // 2
                box = (left, 0, left + new_width, img_h)
            else:
                # 图片太高，裁剪高度
                new_height = int(img_w / target_ratio)
                top = (img_h - new_height) // 2
                box = (0, top, img_w, top + new_height)

            cropped = img.crop(box)

            fmt = img.format or "JPEG"
            if fmt == "JPEG" and cropped.mode == "RGBA":
                cropped = cropped.convert("RGB")

            cropped.save(output_path, format=fmt, quality=95)

        return output_path

    def prepare_for_platform(
        self,
        input_path: str,
        platform: str,
        output_path: Optional[str] = None,
    ) -> str:
        """为特定平台处理图片.

        根据平台要求自动进行裁剪、调整尺寸和压缩。

        Args:
            input_path: 输入图片路径
            platform: 平台名称（wechat/bilibili/xiaohongshu/zhihu）
            output_path: 输出路径，None则自动生成

        Returns:
            处理后的图片路径

        Raises:
            ValueError: 不支持的平台时抛出
        """
        if platform not in PLATFORM_REQUIREMENTS:
            raise ValueError(
                f"不支持的平台: {platform}，"
                f"支持: {list(PLATFORM_REQUIREMENTS.keys())}"
            )

        reqs = PLATFORM_REQUIREMENTS[platform]

        # 生成输出路径
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_{platform}{ext}"

        # 步骤1: 裁剪到目标比例（如果有固定比例）
        if reqs["ratio"] is not None:
            temp_path = output_path + ".tmp"
            self.crop_to_ratio(input_path, temp_path, reqs["ratio"])
            current_path = temp_path
        else:
            current_path = input_path

        try:
            # 步骤2: 调整尺寸到最小要求
            info = self.get_image_info(current_path)
            if info.width < reqs["min_size"] or info.height < reqs["min_size"]:
                # 需要放大
                if info.width >= info.height:
                    self.resize_image(
                        current_path, output_path, width=reqs["min_size"]
                    )
                else:
                    self.resize_image(
                        current_path, output_path, height=reqs["min_size"]
                    )
                current_path = output_path

            # 步骤3: 压缩到平台限制大小
            max_mb = reqs["max_size_bytes"] / (1024 * 1024)
            info = self.get_image_info(current_path)
            if info.size > reqs["max_size_bytes"]:
                self.compress_image(
                    current_path, output_path, max_size_mb=max_mb
                )
            elif current_path != output_path:
                # 复制到最终路径
                with Image.open(current_path) as img:
                    img.save(output_path, quality=95)

            return output_path
        finally:
            # 清理临时文件
            temp_path = output_path + ".tmp"
            if os.path.exists(temp_path):
                os.remove(temp_path)
