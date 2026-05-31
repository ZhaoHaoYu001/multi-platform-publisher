"""媒体管理器模块.

本模块提供了统一管理图片和视频的功能。
"""

import os
import shutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .image_processor import ImageInfo, ImageProcessor, PLATFORM_REQUIREMENTS
from .video_processor import FFmpegNotFoundError, VideoInfo, VideoProcessor


class MediaType(Enum):
    """媒体类型枚举."""

    IMAGE = "image"
    VIDEO = "video"


@dataclass
class MediaItem:
    """媒体项数据类.

    Attributes:
        path: 文件路径
        media_type: 媒体类型
        caption: 说明文字
        order: 排序序号
        image_info: 图片信息（如果是图片）
        video_info: 视频信息（如果是视频）
        thumbnail_path: 缩略图路径
    """

    path: str
    media_type: MediaType
    caption: str = ""
    order: int = 0
    image_info: Optional[ImageInfo] = None
    video_info: Optional[VideoInfo] = None
    thumbnail_path: Optional[str] = None

    @property
    def filename(self) -> str:
        """获取文件名."""
        return os.path.basename(self.path)

    @property
    def exists(self) -> bool:
        """检查文件是否存在."""
        return os.path.exists(self.path)


class MediaManager:
    """媒体管理器，统一管理图片和视频.

    使用示例:
        manager = MediaManager()

        # 添加媒体
        manager.add_image("photo.jpg", caption="风景照片")
        manager.add_video("video.mp4", caption="旅行视频")

        # 生成缩略图
        manager.generate_thumbnails()

        # 为平台批量处理
        results = manager.process_for_platform("wechat")
    """

    def __init__(self, workspace_dir: Optional[str] = None) -> None:
        """初始化媒体管理器.

        Args:
            workspace_dir: 工作目录，None则使用临时目录
        """
        self._workspace_dir = workspace_dir or os.path.join(os.getcwd(), "media_workspace")
        self._items: List[MediaItem] = []
        self._image_processor = ImageProcessor()
        self._video_processor = VideoProcessor()

        # 确保工作目录存在
        os.makedirs(self._workspace_dir, exist_ok=True)

    @property
    def workspace_dir(self) -> str:
        """获取工作目录路径."""
        return self._workspace_dir

    @property
    def items(self) -> List[MediaItem]:
        """获取所有媒体项列表."""
        return sorted(self._items, key=lambda x: x.order)

    @property
    def images(self) -> List[MediaItem]:
        """获取所有图片项."""
        return [item for item in self._items if item.media_type == MediaType.IMAGE]

    @property
    def videos(self) -> List[MediaItem]:
        """获取所有视频项."""
        return [item for item in self._items if item.media_type == MediaType.VIDEO]

    @property
    def count(self) -> int:
        """获取媒体总数."""
        return len(self._items)

    def add_image(
        self,
        path: str,
        caption: str = "",
        order: Optional[int] = None,
        copy_to_workspace: bool = False,
    ) -> MediaItem:
        """添加图片到工作区.

        Args:
            path: 图片文件路径
            caption: 说明文字
            order: 排序序号，None则自动分配
            copy_to_workspace: 是否复制到工作目录

        Returns:
            创建的MediaItem

        Raises:
            FileNotFoundError: 文件不存在时抛出
            ValueError: 非图片文件时抛出
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"图片文件不存在: {path}")

        # 验证是否为有效图片
        try:
            info = self._image_processor.get_image_info(path)
        except Exception as e:
            raise ValueError(f"无效的图片文件: {e}")

        # 复制到工作目录
        if copy_to_workspace:
            dest_path = os.path.join(self._workspace_dir, os.path.basename(path))
            shutil.copy2(path, dest_path)
            path = dest_path

        item = MediaItem(
            path=path,
            media_type=MediaType.IMAGE,
            caption=caption,
            order=order if order is not None else len(self._items),
            image_info=info,
        )

        self._items.append(item)
        return item

    def add_video(
        self,
        path: str,
        caption: str = "",
        order: Optional[int] = None,
        copy_to_workspace: bool = False,
        generate_thumbnail: bool = True,
    ) -> MediaItem:
        """添加视频到工作区.

        Args:
            path: 视频文件路径
            caption: 说明文字
            order: 排序序号，None则自动分配
            copy_to_workspace: 是否复制到工作目录
            generate_thumbnail: 是否自动生成缩略图

        Returns:
            创建的MediaItem

        Raises:
            FileNotFoundError: 文件不存在时抛出
            FFmpegNotFoundError: ffmpeg未安装时抛出
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"视频文件不存在: {path}")

        # 获取视频信息
        try:
            info = self._video_processor.get_video_info(path)
        except FFmpegNotFoundError:
            raise
        except Exception as e:
            raise ValueError(f"无效的视频文件: {e}")

        # 复制到工作目录
        if copy_to_workspace:
            dest_path = os.path.join(self._workspace_dir, os.path.basename(path))
            shutil.copy2(path, dest_path)
            path = dest_path

        # 生成缩略图
        thumbnail_path = None
        if generate_thumbnail and self._video_processor.check_ffmpeg():
            thumb_name = f"thumb_{os.path.splitext(os.path.basename(path))[0]}.jpg"
            thumbnail_path = os.path.join(self._workspace_dir, thumb_name)
            try:
                self._video_processor.extract_thumbnail(path, thumbnail_path, time=1.0)
            except Exception:
                thumbnail_path = None

        item = MediaItem(
            path=path,
            media_type=MediaType.VIDEO,
            caption=caption,
            order=order if order is not None else len(self._items),
            video_info=info,
            thumbnail_path=thumbnail_path,
        )

        self._items.append(item)
        return item

    def remove_item(self, path: str) -> bool:
        """移除媒体项.

        Args:
            path: 文件路径

        Returns:
            是否成功移除
        """
        for i, item in enumerate(self._items):
            if item.path == path:
                self._items.pop(i)
                return True
        return False

    def clear(self) -> None:
        """清空所有媒体项."""
        self._items.clear()

    def reorder(self, path: str, new_order: int) -> None:
        """调整媒体项排序.

        Args:
            path: 文件路径
            new_order: 新的排序序号
        """
        for item in self._items:
            if item.path == path:
                item.order = new_order
                break

    def update_caption(self, path: str, caption: str) -> None:
        """更新媒体项说明文字.

        Args:
            path: 文件路径
            caption: 新的说明文字
        """
        for item in self._items:
            if item.path == path:
                item.caption = caption
                break

    def generate_thumbnails(self) -> Dict[str, str]:
        """为所有视频生成缩略图.

        Returns:
            文件路径到缩略图路径的映射
        """
        results: Dict[str, str] = {}

        for item in self._items:
            if item.media_type == MediaType.VIDEO:
                if self._video_processor.check_ffmpeg():
                    thumb_name = f"thumb_{os.path.splitext(item.filename)[0]}.jpg"
                    thumb_path = os.path.join(self._workspace_dir, thumb_name)
                    try:
                        self._video_processor.extract_thumbnail(
                            item.path, thumb_path, time=1.0
                        )
                        item.thumbnail_path = thumb_path
                        results[item.path] = thumb_path
                    except Exception:
                        pass

        return results

    def process_for_platform(
        self,
        platform: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, str]:
        """为特定平台批量处理媒体.

        Args:
            platform: 平台名称
            output_dir: 输出目录，None则使用工作目录

        Returns:
            原始路径到处理后路径的映射

        Raises:
            ValueError: 不支持的平台时抛出
        """
        output_dir = output_dir or self._workspace_dir
        os.makedirs(output_dir, exist_ok=True)

        # 校验平台名称
        if platform not in PLATFORM_REQUIREMENTS:
            raise ValueError(
                f"不支持的平台: {platform}，"
                f"支持: {list(PLATFORM_REQUIREMENTS.keys())}"
            )

        results: Dict[str, str] = {}

        for item in self._items:
            if item.media_type == MediaType.IMAGE:
                output_path = os.path.join(
                    output_dir,
                    f"{os.path.splitext(item.filename)[0]}_{platform}.jpg",
                )
                try:
                    processed = self._image_processor.prepare_for_platform(
                        item.path, platform, output_path
                    )
                    results[item.path] = processed
                except Exception as e:
                    results[item.path] = f"ERROR: {e}"
            elif item.media_type == MediaType.VIDEO:
                # 视频暂时只返回原路径（视频压缩较慢，按需处理）
                results[item.path] = item.path

        return results

    def upload_to_platform(
        self,
        platform: str,
        credentials: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """将处理后的媒体上传到平台.

        Args:
            platform: 平台名称
            credentials: 平台凭证

        Returns:
            本地路径到远程URL的映射
        """
        from ..adapters.registry import AdapterRegistry
        from ..core.rule_engine import RuleEngine

        credentials = credentials or {}
        results: Dict[str, str] = {}

        # 使用适配器上传
        rule_engine = RuleEngine()
        registry = AdapterRegistry(rule_engine)

        # 注册适配器
        from ..adapters.wechat_adapter import WechatAdapter
        from ..adapters.zhihu_adapter import ZhihuAdapter
        from ..adapters.bilibili_adapter import BilibiliAdapter
        from ..adapters.xiaohongshu_adapter import XiaohongshuAdapter

        registry.register("wechat", WechatAdapter)
        registry.register("zhihu", ZhihuAdapter)
        registry.register("bilibili", BilibiliAdapter)
        registry.register("xiaohongshu", XiaohongshuAdapter)

        adapter = registry.get(platform, credentials)
        if adapter and hasattr(adapter, 'upload_media'):
            image_paths = [item.path for item in self.images if item.exists]
            try:
                uploaded = adapter.upload_media(image_paths)
                results.update(uploaded or {})
            except Exception as e:
                results = {p: f"ERROR: {e}" for p in image_paths}

        return results

    def get_summary(self) -> str:
        """获取媒体摘要信息.

        Returns:
            格式化的摘要字符串
        """
        image_count = len(self.images)
        video_count = len(self.videos)

        total_size = 0
        for item in self._items:
            if item.image_info:
                total_size += item.image_info.size
            elif item.video_info:
                total_size += item.video_info.size

        total_mb = total_size / (1024 * 1024)

        return (
            f"媒体总数: {self.count}\n"
            f"  - 图片: {image_count} 张\n"
            f"  - 视频: {video_count} 个\n"
            f"总大小: {total_mb:.2f} MB"
        )

    def __len__(self) -> int:
        """返回媒体项数量."""
        return self.count

    def __repr__(self) -> str:
        """返回管理器的字符串表示."""
        return (
            f"<MediaManager(images={len(self.images)}, "
            f"videos={len(self.videos)})>"
        )
