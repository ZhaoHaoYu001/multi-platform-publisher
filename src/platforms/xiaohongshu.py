"""小红书平台实现模块.

本模块提供了小红书的内容发布功能。
"""

import re
from typing import Any, List

from ..core.platform_base import PlatformBase, PublishResult


class XiaohongshuPlatform(PlatformBase):
    """小红书平台实现.

    平台特性：
    - 标题限制：20字符
    - 内容限制：1000字符
    - 内容类型：plain（纯文本）
    - 图片限制：9张
    - 特殊处理：自动添加emoji和话题标签

    Attributes:
        name: 平台名称，固定为 "xiaohongshu"
        max_title_length: 标题最大长度，20字符
        max_content_length: 内容最大长度，1000字符
        max_images: 最大图片数量，9张
        content_type: 内容类型，plain
    """

    name: str = "xiaohongshu"
    max_title_length: int = 20
    max_content_length: int = 1000
    max_images: int = 9
    content_type: str = "plain"

    # 常用emoji映射
    EMOJI_MAP = {
        "推荐": "👍",
        "分享": "💡",
        "教程": "📚",
        "干货": "✨",
        "必备": "🔥",
        "好看": "😍",
        "好吃": "😋",
        "好用": "💯",
        "避坑": "⚠️",
        "攻略": "📝",
        "合集": "📦",
        "种草": "🌱",
        "测评": "📊",
        "对比": "⚖️",
        "清单": "📋",
    }

    def __init__(self, cookie: str = "") -> None:
        """初始化小红书平台.

        Args:
            cookie: 小红书登录cookie
        """
        super().__init__()
        self.cookie = cookie

    def adapt_title(self, title: str) -> str:
        """适配标题为小红书格式.

        小红书标题限制20字符，自动添加emoji。

        Args:
            title: 原始标题

        Returns:
            适配后的小红书标题
        """
        # 调用父类的标题截断
        title = super().adapt_title(title)

        # 添加合适的emoji
        for keyword, emoji in self.EMOJI_MAP.items():
            if keyword in title:
                title = f"{emoji} {title}"
                break

        return title

    def adapt_content(self, content: str) -> str:
        """适配内容为小红书纯文本格式.

        将Markdown转换为纯文本，并自动添加emoji和话题标签。

        Args:
            content: Markdown格式的内容

        Returns:
            小红书纯文本格式的内容
        """
        # 先调用父类的基础适配（包含长度截断）
        content = super().adapt_content(content)

        # Markdown转纯文本
        content = self._markdown_to_plain(content)

        # 添加emoji装饰
        content = self._add_emojis(content)

        # 添加话题标签
        content = self._add_hashtags(content)

        return content

    def _markdown_to_plain(self, content: str) -> str:
        """将Markdown转换为纯文本.

        Args:
            content: Markdown格式的内容

        Returns:
            纯文本内容
        """
        # 移除标题标记，保留内容
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)

        # 移除粗体/斜体标记，保留内容
        content = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', content)

        # 移除代码块标记
        content = re.sub(r'```\w*\n?', '', content)
        content = re.sub(r'`([^`]+)`', r'\1', content)

        # 移除链接，保留文本
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

        # 移除图片标记
        content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[\1图片]', content)

        # 移除引用标记
        content = re.sub(r'^>\s+', '', content, flags=re.MULTILINE)

        # 移除列表标记
        content = re.sub(r'^[\s]*[-*+]\s+', '• ', content, flags=re.MULTILINE)
        content = re.sub(r'^\d+\.\s+', '', content, flags=re.MULTILINE)

        # 移除分割线
        content = re.sub(r'^---+$', '', content, flags=re.MULTILINE)

        # 清理多余空行
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content.strip()

    def _add_emojis(self, content: str) -> str:
        """为内容添加emoji装饰.

        Args:
            content: 纯文本内容

        Returns:
            添加emoji后的内容
        """
        lines = content.split('\n')
        decorated_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                decorated_lines.append('')
                continue

            # 为段落开头添加emoji
            for keyword, emoji in self.EMOJI_MAP.items():
                if keyword in line and not line.startswith(emoji):
                    line = f"{emoji} {line}"
                    break

            decorated_lines.append(line)

        return '\n'.join(decorated_lines)

    def _add_hashtags(self, content: str) -> str:
        """为内容添加话题标签.

        Args:
            content: 纯文本内容

        Returns:
            添加话题标签后的内容
        """
        # 从内容中提取关键词作为话题标签
        hashtags = []
        keywords = ["教程", "攻略", "分享", "推荐", "必备", "干货", "合集", "清单"]

        for keyword in keywords:
            if keyword in content and len(hashtags) < 3:
                hashtags.append(f"#{keyword}#")

        # 如果没有找到关键词，添加通用标签
        if not hashtags:
            hashtags = ["#分享#", "#推荐#"]

        # 在内容末尾添加话题标签
        hashtags_str = " ".join(hashtags)
        content = f"{content}\n\n{hashtags_str}"

        return content

    def _do_publish(
        self,
        title: str,
        content: str,
        images: List[str],
        **kwargs: Any,
    ) -> PublishResult:
        """执行小红书发布.

        Args:
            title: 适配后的标题
            content: 适配后的内容（纯文本格式，含emoji和话题标签）
            images: 图片路径列表
            **kwargs: 其他参数

        Returns:
            发布结果
        """
        # 凭证检查
        if not self.cookie:
            return PublishResult(
                success=False,
                platform=self.name,
                message="未配置小红书凭证（cookie）",
            )

        try:
            from ..api.xiaohongshu_api import XiaohongshuAPI

            api = XiaohongshuAPI(cookie=self.cookie)

            # 上传图片
            image_urls = []
            for img_path in images:
                url = api.upload_image(img_path)
                if url:
                    image_urls.append(url)

            # 提取话题标签
            topics = kwargs.get("topics", [])

            # 发布
            result = api.create_and_publish(
                title=title,
                content=content,
                image_urls=image_urls,
                topics=topics,
            )

            return PublishResult(
                success=result["success"],
                platform=self.name,
                message=result["message"],
                raw_response=result,
            )
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.name,
                message=f"小红书发布异常: {e}",
            )

    def check_login(self) -> bool:
        """检查小红书登录状态.

        Returns:
            是否已登录
        """
        if not self.cookie:
            return False

        try:
            from ..api.xiaohongshu_api import XiaohongshuAPI

            api = XiaohongshuAPI(cookie=self.cookie)
            return api.check_login()
        except Exception:
            return False
