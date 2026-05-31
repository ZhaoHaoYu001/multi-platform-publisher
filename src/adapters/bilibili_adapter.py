"""B站适配器."""
from typing import Any, Dict, List, Optional
from .base_adapter import PlatformAdapter, AdaptationResult
from ..core.platform_base import PublishResult
from ..core.rule_engine import RuleEngine

class BilibiliAdapter(PlatformAdapter):
    platform_name = "bilibili"

    def deliver(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        sess_data = self._credentials.get("sess_data", "")
        if sess_data:
            return self._deliver_via_api(adapted, images, **kwargs)
        return self._deliver_via_rpa(adapted, images, **kwargs)

    def _deliver_via_api(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        from ..api.bilibili_api import BilibiliAPI
        api = BilibiliAPI(sess_data=self._credentials.get("sess_data", ""), csrf=self._credentials.get("csrf", ""))
        try:
            result = api.publish_article(title=adapted.title, content=adapted.content, images=images)
            return PublishResult(success=True, platform=self.platform_name, message="API发布成功", url=result.get("url"))
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_name, message=f"API发布失败: {e}")

    def _deliver_via_rpa(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        from ..rpa.bilibili_rpa import BilibiliRPA
        try:
            rpa = BilibiliRPA()
            with rpa:
                result = rpa.publish(title=adapted.title, content=adapted.content, images=images)
            return PublishResult(success=result.get("success", False), platform=self.platform_name, message=result.get("message", ""))
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_name, message=f"RPA发布失败: {e}")
