"""小红书适配器."""
from typing import Any, Dict, List, Optional
from .base_adapter import PlatformAdapter, AdaptationResult
from ..core.platform_base import PublishResult
from ..core.rule_engine import RuleEngine

class XiaohongshuAdapter(PlatformAdapter):
    platform_name = "xiaohongshu"

    def deliver(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        cookie = self._credentials.get("cookie", "")
        if cookie:
            return self._deliver_via_api(adapted, images, **kwargs)
        return self._deliver_via_rpa(adapted, images, **kwargs)

    def _deliver_via_api(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        from ..api.xiaohongshu_api import XiaohongshuAPI
        api = XiaohongshuAPI(cookie=self._credentials.get("cookie", ""))
        try:
            result = api.create_and_publish(title=adapted.title, content=adapted.content, images=images)
            return PublishResult(success=True, platform=self.platform_name, message="API发布成功", url=result.get("url"))
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_name, message=f"API发布失败: {e}")

    def _deliver_via_rpa(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        from ..rpa.xiaohongshu_rpa import XiaohongshuRPA
        try:
            rpa = XiaohongshuRPA()
            with rpa:
                result = rpa.publish(title=adapted.title, content=adapted.content, images=images)
            return PublishResult(success=result.get("success", False), platform=self.platform_name, message=result.get("message", ""))
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_name, message=f"RPA发布失败: {e}")
