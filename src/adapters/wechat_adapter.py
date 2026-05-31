"""微信公众号适配器."""
from typing import Any, Dict, List, Optional
from .base_adapter import PlatformAdapter, AdaptationResult
from ..core.platform_base import PublishResult
from ..core.rule_engine import RuleEngine

class WechatAdapter(PlatformAdapter):
    platform_name = "wechat"

    def deliver(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        from ..api.wechat_api import WechatAPI
        api = WechatAPI(
            app_id=self._credentials.get("app_id", ""),
            app_secret=self._credentials.get("app_secret", ""),
        )
        try:
            cover_path = images[0] if images else None
            result = api.publish_article(
                title=adapted.title,
                content=adapted.content,
                author=kwargs.get("author", ""),
                digest=adapted.content[:120] if adapted.content else "",
                cover_image_path=cover_path,
            )
            return PublishResult(success=True, platform=self.platform_name, message="发布成功", url=result.get("url"))
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_name, message=f"发布失败: {e}")
