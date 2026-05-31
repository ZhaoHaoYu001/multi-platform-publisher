"""统一发布管线.

标准化发布流程: 解析 → 适配 → 图片处理 → 媒体上传 → 投递。
每个阶段独立可替换，支持自定义阶段组合。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..adapters.base_adapter import AdaptationResult, PlatformAdapter
from ..core.content_document import ContentDocument, ImageRef
from ..core.content_parser import ContentParser
from ..core.platform_base import PublishMode, PublishResult
from ..core.rule_engine import RuleEngine


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
    """图片处理阶段: 按平台 YAML 规则裁剪/压缩图片.

    读取 RuleEngine 中的 media 规则，自动进行:
    - 按比例裁剪（image_ratio）
    - 最小尺寸调整（image_min_size）
    - 文件大小压缩（image_max_size_mb）
    """

    def __init__(self, rule_engine: Optional[RuleEngine] = None) -> None:
        self._rule_engine = rule_engine

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        from ..media.image_processor import ImageProcessor, PLATFORM_REQUIREMENTS

        processor = ImageProcessor()
        processed: List[str] = []

        # 收集所有图片来源
        image_sources = [img.src for img in ctx.document.images]
        image_sources.extend(ctx.metadata.get("images", []))

        if not image_sources:
            ctx.processed_images = []
            return ctx

        # 获取平台媒体规则
        platform_reqs = PLATFORM_REQUIREMENTS.get(ctx.platform, {})

        for img_path in image_sources:
            try:
                if not img_path or not _is_local_file(img_path):
                    # URL 或无效路径，直接保留
                    processed.append(img_path)
                    continue

                output_path = processor.prepare_for_platform(img_path, ctx.platform)
                processed.append(output_path)
            except Exception as e:
                ctx.errors.append(f"图片处理失败 {img_path}: {e}")
                processed.append(img_path)  # 处理失败则使用原图

        ctx.processed_images = processed
        return ctx


class MediaUploadStage(PublishStage):
    """媒体上传阶段: 将处理后的图片上传到平台.

    调用适配器的 upload_media 方法（如果存在），
    否则跳过上传，直接在投递阶段处理。
    """

    def __init__(self, adapter: PlatformAdapter) -> None:
        self._adapter = adapter

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        images = ctx.processed_images or ctx.metadata.get("images", [])

        if not images:
            ctx.uploaded_media = {}
            return ctx

        # 如果适配器有 upload_media 方法，调用它
        if hasattr(self._adapter, 'upload_media'):
            try:
                uploaded = self._adapter.upload_media(images)
                ctx.uploaded_media = uploaded or {}
            except Exception as e:
                ctx.errors.append(f"媒体上传失败: {e}")
                ctx.uploaded_media = {}
        else:
            # 没有专用上传方法，标记为待投递阶段处理
            ctx.uploaded_media = {img: img for img in images}

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


def _is_local_file(path: str) -> bool:
    """检查路径是否为本地文件."""
    import os
    return os.path.exists(path) and os.path.isfile(path)


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
        rule_engine: Optional[RuleEngine] = None,
    ) -> "PublishPipeline":
        """创建默认管线: 解析 → 适配 → 图片处理 → 媒体上传 → 投递.

        Args:
            adapter: 平台适配器
            title: 文章标题
            tags: 标签列表
            rule_engine: 规则引擎（用于图片处理规则）

        Returns:
            PublishPipeline 实例
        """
        return cls([
            ParseStage(title=title, tags=tags),
            AdaptStage(adapter),
            ImageProcessStage(rule_engine=rule_engine),
            MediaUploadStage(adapter),
            DeliverStage(adapter),
        ])

    @classmethod
    def create_custom(
        cls,
        stages: List[PublishStage],
    ) -> "PublishPipeline":
        """创建自定义管线.

        Args:
            stages: 自定义阶段列表

        Returns:
            PublishPipeline 实例
        """
        return cls(stages)
