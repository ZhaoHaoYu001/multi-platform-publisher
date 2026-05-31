"""平台基础数据结构模块.

本模块提供了：
- PublishMode: 发布模式枚举（模拟/真实）
- PublishResult: 发布结果数据类
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


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
        status = "[OK] Success" if self.success else "[FAIL] Failed"
        return f"[{self.platform}] {status}: {self.message}"
