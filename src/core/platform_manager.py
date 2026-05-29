"""平台管理器模块，负责管理多个平台的注册和发布.

本模块提供了：
- PlatformManager: 平台管理器，统一管理所有平台
"""

from typing import Any, Dict, List, Optional

from .platform_base import PlatformBase, PublishMode, PublishResult


class PlatformManager:
    """平台管理器，负责平台的注册、注销和批量发布.

    使用示例:
        manager = PlatformManager()
        manager.register(WechatPlatform())
        manager.register(ZhihuPlatform())

        # 发布到所有平台
        results = manager.publish_to_all(title="标题", content="内容")

        # 发布到指定平台
        results = manager.publish_to_selected(
            platforms=["wechat", "zhihu"],
            title="标题",
            content="内容"
        )
    """

    def __init__(self) -> None:
        """初始化平台管理器."""
        self._platforms: Dict[str, PlatformBase] = {}

    @property
    def platforms(self) -> List[str]:
        """获取已注册的平台名称列表.

        Returns:
            平台名称列表
        """
        return list(self._platforms.keys())

    @property
    def count(self) -> int:
        """获取已注册的平台数量.

        Returns:
            平台数量
        """
        return len(self._platforms)

    def register(self, platform: PlatformBase) -> None:
        """注册平台.

        Args:
            platform: 平台实例

        Raises:
            TypeError: 如果platform不是PlatformBase的子类
            ValueError: 如果平台名称已存在
        """
        if not isinstance(platform, PlatformBase):
            raise TypeError(
                f"平台必须是PlatformBase的子类，当前类型: {type(platform)}"
            )

        if platform.name in self._platforms:
            raise ValueError(f"平台 '{platform.name}' 已注册")

        self._platforms[platform.name] = platform

    def unregister(self, platform_name: str) -> None:
        """注销平台.

        Args:
            platform_name: 平台名称

        Raises:
            KeyError: 如果平台不存在
        """
        if platform_name not in self._platforms:
            raise KeyError(f"平台 '{platform_name}' 未注册")

        del self._platforms[platform_name]

    def get_platform(self, platform_name: str) -> Optional[PlatformBase]:
        """获取平台实例.

        Args:
            platform_name: 平台名称

        Returns:
            平台实例，如果不存在返回None
        """
        return self._platforms.get(platform_name)

    def has_platform(self, platform_name: str) -> bool:
        """检查平台是否已注册.

        Args:
            platform_name: 平台名称

        Returns:
            是否已注册
        """
        return platform_name in self._platforms

    def publish_to_platform(
        self,
        platform_name: str,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
        mode: PublishMode = PublishMode.SIMULATE,
        **kwargs: Any,
    ) -> PublishResult:
        """发布内容到指定平台.

        Args:
            platform_name: 平台名称
            title: 文章标题
            content: 文章内容
            images: 图片路径列表
            mode: 发布模式
            **kwargs: 其他平台特定参数

        Returns:
            发布结果

        Raises:
            KeyError: 如果平台不存在
        """
        platform = self.get_platform(platform_name)
        if platform is None:
            return PublishResult(
                success=False,
                platform=platform_name,
                message=f"平台 '{platform_name}' 未注册",
            )

        return platform.publish(
            title=title,
            content=content,
            images=images,
            mode=mode,
            **kwargs,
        )

    def publish_to_all(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
        mode: PublishMode = PublishMode.SIMULATE,
        **kwargs: Any,
    ) -> Dict[str, PublishResult]:
        """发布内容到所有已注册平台.

        Args:
            title: 文章标题
            content: 文章内容
            images: 图片路径列表
            mode: 发布模式
            **kwargs: 其他平台特定参数

        Returns:
            各平台发布结果的字典，key为平台名称
        """
        results: Dict[str, PublishResult] = {}

        for name, platform in self._platforms.items():
            results[name] = platform.publish(
                title=title,
                content=content,
                images=images,
                mode=mode,
                **kwargs,
            )

        return results

    def publish_to_selected(
        self,
        platforms: List[str],
        title: str,
        content: str,
        images: Optional[List[str]] = None,
        mode: PublishMode = PublishMode.SIMULATE,
        **kwargs: Any,
    ) -> Dict[str, PublishResult]:
        """发布内容到指定的多个平台.

        Args:
            platforms: 平台名称列表
            title: 文章标题
            content: 文章内容
            images: 图片路径列表
            mode: 发布模式
            **kwargs: 其他平台特定参数

        Returns:
            各平台发布结果的字典，key为平台名称
        """
        results: Dict[str, PublishResult] = {}

        for name in platforms:
            if name in self._platforms:
                results[name] = self._platforms[name].publish(
                    title=title,
                    content=content,
                    images=images,
                    mode=mode,
                    **kwargs,
                )
            else:
                results[name] = PublishResult(
                    success=False,
                    platform=name,
                    message=f"平台 '{name}' 未注册",
                )

        return results

    def get_summary(self, results: Dict[str, PublishResult]) -> str:
        """生成发布结果摘要.

        Args:
            results: 发布结果字典

        Returns:
            格式化的摘要字符串
        """
        total = len(results)
        success = sum(1 for r in results.values() if r.success)
        failed = total - success

        lines = [
            f"发布完成: {success}/{total} 成功",
            "-" * 40,
        ]

        for name, result in results.items():
            lines.append(f"  {result}")

        if failed > 0:
            lines.append("-" * 40)
            lines.append(f"失败平台: {failed} 个")

        return "\n".join(lines)

    def __len__(self) -> int:
        """返回已注册平台数量."""
        return self.count

    def __contains__(self, platform_name: str) -> bool:
        """支持 in 操作符检查平台是否存在."""
        return self.has_platform(platform_name)

    def __repr__(self) -> str:
        """返回管理器的字符串表示."""
        return f"<PlatformManager(platforms={self.platforms})>"
