"""平台适配器基类.

将「格式适配」与「内容投递」解耦。
适配器组合规则引擎进行内容变换，子类实现 deliver() 完成平台投递。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core.content_document import ContentDocument, ImageRef
from ..core.platform_base import PublishMode, PublishResult
from ..core.rule_engine import RuleEngine


@dataclass
class AdaptationResult:
    """适配结果."""
    title: str
    content: str
    images: List[ImageRef] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PlatformAdapter(ABC):
    """平台适配器基类.

    子类需实现:
    - platform_name: 平台名称
    - deliver(): 实际投递逻辑
    """

    platform_name: str = ""

    def __init__(self, rule_engine: RuleEngine, credentials: Optional[Dict[str, str]] = None) -> None:
        self._rule_engine = rule_engine
        self._credentials = credentials or {}

    def adapt(self, doc: ContentDocument) -> AdaptationResult:
        """完整适配流程."""
        adapted_title = self._rule_engine.adapt_title(doc.title, self.platform_name)
        adapted_content = self._rule_engine.adapt_content(doc, self.platform_name)
        warnings = self._rule_engine.validate(doc, self.platform_name)
        return AdaptationResult(
            title=adapted_title,
            content=adapted_content,
            images=doc.images,
            warnings=warnings,
        )

    @abstractmethod
    def deliver(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        """实际投递逻辑，子类必须实现."""
        ...

    def publish(self, doc: ContentDocument, images: List[str], mode: PublishMode, **kwargs: Any) -> PublishResult:
        """完整发布流程: 适配 -> 投递."""
        adapted = self.adapt(doc)
        if mode == PublishMode.SIMULATE:
            return self._simulate(adapted)
        return self.deliver(adapted, images, **kwargs)

    def _simulate(self, adapted: AdaptationResult) -> PublishResult:
        """模拟发布."""
        message = (
            f"[模拟发布] 标题: {adapted.title[:30]}...\n"
            f"  - 内容长度: {len(adapted.content)} 字符\n"
            f"  - 图片数量: {len(adapted.images)} 张\n"
            f"  - 警告: {len(adapted.warnings)} 条"
        )
        if adapted.warnings:
            message += "\n  - " + "\n  - ".join(adapted.warnings)
        return PublishResult(success=True, platform=self.platform_name, message=message)
