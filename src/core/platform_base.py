"""平台基类模块，定义所有平台的通用接口和数据结构.

本模块提供了：
- PublishMode: 发布模式枚举（模拟/真实）
- PublishResult: 发布结果数据类
- PlatformBase: 平台基类抽象类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PublishMode(Enum):
    """发布模式枚举.

    Attributes:
        SIMULATE: 模拟模式，不实际发布，仅验证和预览
        REAL: 真实模式，实际发布到平台
    """

    SIMULATE = "simulate"
    REAL = "real"


@dataclass
class PublishResult:
    """发布结果数据类.

    Attributes:
        success: 是否发布成功
        platform: 平台名称
        message: 结果消息
        url: 发布成功后的内容URL（如果有的话）
        published_at: 发布时间
        raw_response: 平台原始响应数据
    """

    success: bool
    platform: str
    message: str
    url: Optional[str] = None
    published_at: datetime = field(default_factory=datetime.now)
    raw_response: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        """返回发布结果的字符串表示."""
        status = "✅ 成功" if self.success else "❌ 失败"
        return f"[{self.platform}] {status}: {self.message}"


class PlatformBase(ABC):
    """平台基类，所有平台实现必须继承此类.

    子类需要实现：
    - name: 平台名称属性
    - _do_publish(): 实际的发布逻辑

    Attributes:
        name: 平台名称
        max_title_length: 标题最大长度限制
        max_content_length: 内容最大长度限制
        max_images: 最大图片数量
        content_type: 内容类型（richtext/markdown/plain）
    """

    # 平台配置（子类应覆盖这些值）
    name: str = "base"
    max_title_length: int = 100
    max_content_length: int = 50000
    max_images: int = 10
    content_type: str = "richtext"

    def __init__(self) -> None:
        """初始化平台基类."""
        self._validate_config()

    def _validate_config(self) -> None:
        """验证平台配置是否有效."""
        if not self.name:
            raise ValueError("平台名称不能为空")
        if self.max_title_length <= 0:
            raise ValueError("标题最大长度必须大于0")
        if self.max_content_length <= 0:
            raise ValueError("内容最大长度必须大于0")
        if self.max_images < 0:
            raise ValueError("图片数量不能为负数")

    def adapt_title(self, title: str) -> str:
        """适配标题到平台限制.

        如果标题超过平台限制，将截断并添加省略号。

        Args:
            title: 原始标题

        Returns:
            适配后的标题
        """
        if len(title) <= self.max_title_length:
            return title
        # 截断并添加省略号
        return title[: self.max_title_length - 3] + "..."

    def adapt_content(self, content: str) -> str:
        """适配内容到平台格式.

        根据平台的内容类型进行格式转换。

        Args:
            content: 原始内容（Markdown格式）

        Returns:
            适配后的内容
        """
        if len(content) <= self.max_content_length:
            return content
        # 截断内容
        truncated = content[: self.max_content_length - 50]
        return truncated + "\n\n...（内容过长，已截断）"

    def validate_images(self, images: List[str]) -> List[str]:
        """验证并处理图片列表.

        Args:
            images: 图片路径列表

        Returns:
            处理后的图片列表

        Raises:
            ValueError: 图片数量超过限制时抛出
        """
        if len(images) > self.max_images:
            raise ValueError(
                f"图片数量({len(images)})超过平台限制({self.max_images})"
            )
        return images

    def publish(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
        mode: PublishMode = PublishMode.SIMULATE,
        **kwargs: Any,
    ) -> PublishResult:
        """发布内容到平台.

        Args:
            title: 文章标题
            content: 文章内容
            images: 图片路径列表
            mode: 发布模式（模拟/真实）
            **kwargs: 其他平台特定参数

        Returns:
            PublishResult: 发布结果
        """
        images = images or []

        # 适配标题和内容
        adapted_title = self.adapt_title(title)
        adapted_content = self.adapt_content(content)

        # 验证图片
        try:
            validated_images = self.validate_images(images)
        except ValueError as e:
            return PublishResult(
                success=False,
                platform=self.name,
                message=str(e),
            )

        # 模拟模式：返回预览结果
        if mode == PublishMode.SIMULATE:
            return self._simulate_publish(
                adapted_title, adapted_content, validated_images
            )

        # 真实模式：调用子类实现
        try:
            return self._do_publish(
                adapted_title, adapted_content, validated_images, **kwargs
            )
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.name,
                message=f"发布失败: {str(e)}",
            )

    def _simulate_publish(
        self, title: str, content: str, images: List[str]
    ) -> PublishResult:
        """模拟发布，返回预览信息.

        Args:
            title: 适配后的标题
            content: 适配后的内容
            images: 图片列表

        Returns:
            模拟发布结果
        """
        preview_info = {
            "title": title,
            "content_length": len(content),
            "images_count": len(images),
            "content_type": self.content_type,
        }

        message = (
            f"[模拟发布] 标题: {title[:20]}...\n"
            f"  - 内容长度: {len(content)} 字符\n"
            f"  - 图片数量: {len(images)} 张\n"
            f"  - 内容类型: {self.content_type}"
        )

        return PublishResult(
            success=True,
            platform=self.name,
            message=message,
            raw_response=preview_info,
        )

    @abstractmethod
    def _do_publish(
        self,
        title: str,
        content: str,
        images: List[str],
        **kwargs: Any,
    ) -> PublishResult:
        """实际发布逻辑，子类必须实现.

        Args:
            title: 适配后的标题
            content: 适配后的内容
            images: 图片列表
            **kwargs: 其他平台特定参数

        Returns:
            发布结果
        """
        pass

    def __repr__(self) -> str:
        """返回平台对象的字符串表示."""
        return f"<{self.__class__.__name__}(name='{self.name}')>"
