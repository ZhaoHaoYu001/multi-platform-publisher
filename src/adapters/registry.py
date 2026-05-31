"""适配器注册中心.

支持动态注册和获取平台适配器。
"""

from typing import Dict, List, Optional, Type

from .base_adapter import PlatformAdapter
from ..core.rule_engine import RuleEngine


class AdapterRegistry:
    """适配器注册中心.

    使用示例:
        registry = AdapterRegistry(RuleEngine())
        registry.register("wechat", WechatAdapter)
        adapter = registry.get("wechat", credentials={"app_id": "xxx"})
    """

    def __init__(self, rule_engine: RuleEngine) -> None:
        self._rule_engine = rule_engine
        self._adapter_classes: Dict[str, Type[PlatformAdapter]] = {}

    def register(self, name: str, adapter_class: Type[PlatformAdapter]) -> None:
        """注册适配器类."""
        self._adapter_classes[name] = adapter_class

    def get(self, name: str, credentials: Optional[Dict[str, str]] = None) -> Optional[PlatformAdapter]:
        """获取适配器实例."""
        cls = self._adapter_classes.get(name)
        if cls is None:
            return None
        return cls(self._rule_engine, credentials)

    def list_platforms(self) -> List[str]:
        """列出所有已注册平台."""
        return list(self._adapter_classes.keys())

    def has_platform(self, name: str) -> bool:
        """检查平台是否已注册."""
        return name in self._adapter_classes
