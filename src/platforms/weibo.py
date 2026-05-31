"""微博平台实现."""

import re
from typing import Any, Dict, List, Optional

from ..core.platform_base import PlatformBase, PublishMode, PublishResult


class WeiboPlatform(PlatformBase):
    """微博平台.

    支持长微博和图片微博，标题限制32字，内容限制2000字。
    支持 GIF 动图，最多18张图片。
    """

    name = "weibo"
    max_title_length = 32
    max_content_length = 2000
    max_images = 18
    content_type = "plain"

    def __init__(self, cookie: str = "") -> None:
        self._cookie = cookie

    def adapt_content(self, title: str, content: str) -> str:
        """适配微博内容格式."""
        text = content

        # Markdown → 纯文本
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[-*]\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'---+', '', text)

        # 微博话题标签（从标签中提取）
        tags = self._extract_tags(title)
        if tags:
            text += "\n\n" + " ".join(f"#{t}#" for t in tags)

        return text.strip()

    def _extract_tags(self, title: str) -> List[str]:
        """从标题中提取关键词作为话题标签."""
        # 简单实现：使用标题中的关键词
        keywords = []
        common_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        for word in title:
            if len(word) >= 2 and word not in common_words:
                keywords.append(word)
        return keywords[:3]

    def _do_publish(self, title: str, content: str, images: List[str], **kwargs: Any) -> PublishResult:
        """发布到微博."""
        if self._cookie:
            return self._publish_via_api(title, content, images, **kwargs)
        return self._publish_via_rpa(title, content, images, **kwargs)

    def _publish_via_api(self, title: str, content: str, images: List[str], **kwargs: Any) -> PublishResult:
        """通过 API 发布."""
        from ..api.weibo_api import WeiboAPI
        api = WeiboAPI(cookie=self._cookie)
        try:
            result = api.create_and_publish(title=title, content=content, images=images)
            return PublishResult(
                success=True,
                platform=self.name,
                message="API发布成功",
                url=result.get("url"),
            )
        except Exception as e:
            return PublishResult(success=False, platform=self.name, message=f"API发布失败: {e}")

    def _publish_via_rpa(self, title: str, content: str, images: List[str], **kwargs: Any) -> PublishResult:
        """通过 RPA 发布."""
        from ..rpa.weibo_rpa import WeiboRPA
        try:
            rpa = WeiboRPA()
            with rpa:
                rpa.login()
                result = rpa.publish(title=title, content=content, images=images)
            return PublishResult(
                success=result.get("success", False),
                platform=self.name,
                message=result.get("message", ""),
            )
        except Exception as e:
            return PublishResult(success=False, platform=self.name, message=f"RPA发布失败: {e}")
