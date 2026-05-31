"""统一发布管线.

标准化发布流程: 解析 → 适配 → 图片处理 → 媒体上传 → 投递。
每个阶段独立可替换，支持自定义阶段组合。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..adapters.base_adapter import AdaptationResult, PlatformAdapter
from ..core.content_document import ContentDocument, ImageRef
from ..core.content_parser import ContentParser
from ..core.platform_base import PublishMode, PublishResult


@dataclass
class PipelineContext:
    """管线上下文，在各阶段间传递状态."""

    document: ContentDocument = field(default_factory=ContentDocument)
    platform: str = ""
    adapted: Optional[AdaptationResult] = None
    processed_images: List[str] = field(default_factory=list)
    uploaded_media: Dict[str, str] = field(default_factory=dict)  # local_path -> remote_url
    result: Optional[PublishResult] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PublishStage(ABC):
    """发布管线阶段基类."""

    @abstractmethod
    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """执行阶段逻辑.

        Args:
            ctx: 管线上下文

        Returns:
            更新后的上下文
        """
        ...


class ParseStage(PublishStage):
    """解析阶段: Markdown → ContentDocument."""

    def __init__(self, title: str = "", tags: Optional[List[str]] = None) -> None:
        self._title = title
        self._tags = tags

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        parser = ContentParser()
        ctx.document = parser.parse(
            ctx.metadata.get("raw_content", ""),
            title=self._title or ctx.metadata.get("title", ""),
            tags=self._tags or ctx.metadata.get("tags"),
        )
        return ctx


class AdaptStage(PublishStage):
    """适配阶段: 使用适配器进行内容变换."""

    def __init__(self, adapter: PlatformAdapter) -> None:
        self._adapter = adapter

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        ctx.adapted = self._adapter.adapt(ctx.document)
        return ctx


class ImageProcessStage(PublishStage):
    """图片处理阶段: 按平台需求裁剪/压缩图片."""

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        import os
        from ..media.image_processor import ImageProcessor

        processor = ImageProcessor()
        processed: List[str] = []

        # 从文档图片引用中获取图片路径
        image_sources = [img.src for img in ctx.document.images]
        # 也包含 metadata 中的图片列表
        image_sources.extend(ctx.metadata.get("images", []))

        for img_path in image_sources:
            if os.path.exists(img_path):
                try:
                    output_path = processor.prepare_for_platform(
                        img_path, ctx.platform
                    )
                    processed.append(output_path)
                except Exception:
                    processed.append(img_path)  # 处理失败则使用原图
            else:
                processed.append(img_path)

        ctx.processed_images = processed
        return ctx


class DeliverStage(PublishStage):
    """投递阶段: 调用适配器的 deliver 方法."""

    def __init__(self, adapter: PlatformAdapter) -> None:
        self._adapter = adapter

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.adapted is None:
            ctx.errors.append("适配结果为空，无法投递")
            return ctx

        images = ctx.processed_images or ctx.metadata.get("images", [])
        mode = ctx.metadata.get("mode", PublishMode.REAL)

        if mode == PublishMode.SIMULATE:
            ctx.result = self._adapter._simulate(ctx.adapted)
        else:
            ctx.result = self._adapter.deliver(ctx.adapted, images)

        return ctx


class PublishPipeline:
    """统一发布管线.

    使用示例:
        pipeline = PublishPipeline([ParseStage(title="t"), AdaptStage(adapter), DeliverStage(adapter)])
        ctx = PipelineContext(metadata={"raw_content": "...", "mode": PublishMode.REAL})
        result = pipeline.execute(ctx)
    """

    def __init__(self, stages: Optional[List[PublishStage]] = None) -> None:
        """初始化管线.

        Args:
            stages: 管线阶段列表。为 None 时使用默认阶段组合。
        """
        self._stages = stages or []

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """执行完整管线.

        Args:
            ctx: 初始管线上下文

        Returns:
            最终管线上下文（包含结果或错误）
        """
        for stage in self._stages:
            ctx = stage.execute(ctx)
            if ctx.errors:
                break
        return ctx

    @classmethod
    def create_default(
        cls,
        adapter: PlatformAdapter,
        title: str = "",
        tags: Optional[List[str]] = None,
    ) -> "PublishPipeline":
        """创建默认管线: 解析 → 适配 → 图片处理 → 投递.

        Args:
            adapter: 平台适配器
            title: 文章标题
            tags: 标签列表

        Returns:
            PublishPipeline 实例
        """
        return cls([
            ParseStage(title=title, tags=tags),
            AdaptStage(adapter),
            ImageProcessStage(),
            DeliverStage(adapter),
        ])
