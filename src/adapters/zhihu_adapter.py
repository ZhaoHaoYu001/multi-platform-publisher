"""知乎适配器."""
from typing import Any, Dict, List, Optional
from .base_adapter import PlatformAdapter, AdaptationResult
from ..core.platform_base import PublishResult
from ..core.rule_engine import RuleEngine

class ZhihuAdapter(PlatformAdapter):
    platform_name = "zhihu"

    def deliver(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        username = self._credentials.get("username", "")
        password = self._credentials.get("password", "")
        if username and password:
            result = self._deliver_via_api(adapted, images, **kwargs)
            if result.success:
                return result
        return self._deliver_via_rpa(adapted, images, **kwargs)

    def _deliver_via_api(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        from ..api.zhihu_api import ZhihuAPI
        api = ZhihuAPI(username=self._credentials.get("username", ""), password=self._credentials.get("password", ""))
        try:
            api.login()
            image_urls = []
            for img in images:
                url = api.upload_image(img)
                if url:
                    image_urls.append(url)
            result = api.create_and_publish(title=adapted.title, content=adapted.content, image_urls=image_urls)
            return PublishResult(success=True, platform=self.platform_name, message="API发布成功", url=result.get("url"))
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_name, message=f"API发布失败: {e}")

    def _deliver_via_rpa(self, adapted: AdaptationResult, images: List[str], **kwargs: Any) -> PublishResult:
        from ..rpa.zhihu_rpa import ZhihuRPA
        try:
            rpa = ZhihuRPA()
            with rpa:
                result = rpa.publish(title=adapted.title, content=adapted.content, images=images)
            return PublishResult(success=result.get("success", False), platform=self.platform_name, message=result.get("message", ""))
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_name, message=f"RPA发布失败: {e}")
