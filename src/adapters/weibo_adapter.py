"""微博适配器."""
from typing import Any, Dict, List, Optional
from .base_adapter import PlatformAdapter, AdaptationResult
from ..core.platform_base import PublishResult
from ..core.rule_engine import RuleEngine


class WeiboAdapter(PlatformAdapter):
    """微博适配器.

    支持 API 和 RPA 两种投递方式。
    凭证: cookie（微博 Cookie）
    """

    platform_name = "weibo"

    def deliver(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        """投递到微博."""
        cookie = self._credentials.get("cookie", "")
        if cookie:
            result = self._deliver_via_api(adapted, images, **kwargs)
            if result.success:
                return result
        return self._deliver_via_rpa(adapted, images, **kwargs)

    def _deliver_via_api(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        """通过 API 投递."""
        from ..api.weibo_api import WeiboAPI
        api = WeiboAPI(cookie=self._credentials.get("cookie", ""))
        try:
            result = api.create_and_publish(
                title=adapted.title,
                content=adapted.content,
                images=images,
            )
            return PublishResult(
                success=True,
                platform=self.platform_name,
                message="API发布成功",
                url=result.get("url"),
            )
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.platform_name,
                message=f"API发布失败: {e}",
            )

    def _deliver_via_rpa(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        """通过 RPA 投递."""
        from ..rpa.weibo_rpa import WeiboRPA
        try:
            rpa = WeiboRPA()
            with rpa:
                result = rpa.publish(
                    title=adapted.title,
                    content=adapted.content,
                    images=images,
                )
            return PublishResult(
                success=result.get("success", False),
                platform=self.platform_name,
                message=result.get("message", ""),
            )
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.platform_name,
                message=f"RPA发布失败: {e}",
            )
