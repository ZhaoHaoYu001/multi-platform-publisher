"""抖音平台实现."""

import re
from typing import Any, Dict, List, Optional

from ..core.platform_base import PlatformBase, PublishMode, PublishResult


class DouyinPlatform(PlatformBase):
    """抖音平台.

    支持图文笔记发布，标题限制30字，内容限制1000字。
    竖版图片为主，自动添加话题标签和互动引导。
    """

    name = "douyin"
    max_title_length = 30
    max_content_length = 1000
    max_images = 35
    content_type = "plain"

    def __init__(self, cookie: str = "") -> None:
        self._cookie = cookie

    def adapt_content(self, title: str, content: str) -> str:
        """适配抖音内容格式."""
        text = content

        # Markdown → 纯文本
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[-*]\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'---+', '', text)

        # 添加 emoji 装饰
        text = self._add_emoji(text)

        # 添加互动引导
        text += "\n\n💬 你觉得呢？欢迎在评论区留言讨论！"

        return text.strip()

    def _add_emoji(self, text: str) -> str:
        """为段落添加 emoji 装饰."""
        lines = text.split('\n')
        result = []
        emoji_map = {
            '总结': '📝', '推荐': '👍', '分享': '📢',
            '注意': '⚠️', '技巧': '💡', '教程': '📚',
        }
        for line in lines:
            if line.strip():
                for keyword, emoji in emoji_map.items():
                    if keyword in line:
                        line = f"{emoji} {line}"
                        break
            result.append(line)
        return '\n'.join(result)

    def _do_publish(self, title: str, content: str, images: List[str], **kwargs: Any) -> PublishResult:
        """发布到抖音."""
        if self._cookie:
            return self._publish_via_api(title, content, images, **kwargs)
        return self._publish_via_rpa(title, content, images, **kwargs)

    def _publish_via_api(self, title: str, content: str, images: List[str], **kwargs: Any) -> PublishResult:
        """通过 API 发布."""
        from ..api.douyin_api import DouyinAPI
        api = DouyinAPI(cookie=self._cookie)
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
        from ..rpa.douyin_rpa import DouyinRPA
        try:
            rpa = DouyinRPA()
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
