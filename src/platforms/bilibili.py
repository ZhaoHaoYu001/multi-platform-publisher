"""B站平台实现模块.

本模块提供了B站（哔哩哔哩）的内容发布功能。
"""

from typing import Any, List

from ..core.platform_base import PlatformBase, PublishResult


class BilibiliPlatform(PlatformBase):
    """B站平台实现.

    平台特性：
    - 标题限制：80字符
    - 内容限制：15000字符
    - 内容类型：richtext
    - 图片限制：100张

    Attributes:
        name: 平台名称，固定为 "bilibili"
        max_title_length: 标题最大长度，80字符
        max_content_length: 内容最大长度，15000字符
        max_images: 最大图片数量，100张
        content_type: 内容类型，richtext
    """

    name: str = "bilibili"
    max_title_length: int = 80
    max_content_length: int = 15000
    max_images: int = 100
    content_type: str = "richtext"

    def __init__(self, sess_data: str = "", csrf: str = "") -> None:
        """初始化B站平台.

        Args:
            sess_data: B站SESSDATA cookie值
            csrf: B站bili_jct CSRF token
        """
        super().__init__()
        self.sess_data = sess_data
        self.csrf = csrf

    def adapt_content(self, content: str) -> str:
        """适配内容为B站专栏格式.

        B站专栏支持富文本格式，将Markdown转换为B站支持的格式。

        Args:
            content: Markdown格式的内容

        Returns:
            B站专栏格式的内容
        """
        # 先调用父类的基础适配
        content = super().adapt_content(content)

        import re

        # B站专栏使用自己的富文本格式
        # 标题转换为加粗+放大
        content = re.sub(r'^### (.+)$', r'**\1**', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'**\1**', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.+)$', r'**\1**', content, flags=re.MULTILINE)

        # 代码块转换为引用+等宽字体
        content = re.sub(
            r'```(\w+)?\n(.*?)```',
            lambda m: f'```\n{m.group(2)}```',
            content,
            flags=re.DOTALL
        )

        # 分割线
        content = re.sub(r'^---+$', '——————', content, flags=re.MULTILINE)

        return content

    def _do_publish(
        self,
        title: str,
        content: str,
        images: List[str],
        **kwargs: Any,
    ) -> PublishResult:
        """执行B站发布.

        有API凭证时走API发布，无凭证时降级到RPA浏览器自动化发布。

        Args:
            title: 适配后的标题
            content: 适配后的内容（Markdown格式，会自动转BBCode）
            images: 图片路径列表
            **kwargs: 其他参数（category, tags, summary）

        Returns:
            发布结果
        """
        # 有凭证走API
        if self.sess_data:
            return self._publish_via_api(title, content, images, **kwargs)

        # 无凭证走RPA
        return self._publish_via_rpa(title, content, images, **kwargs)

    def _publish_via_api(
        self, title: str, content: str, images: List[str], **kwargs: Any
    ) -> PublishResult:
        """通过API发布B站专栏."""
        try:
            from ..api.bilibili_api import BilibiliAPI

            api = BilibiliAPI(sess_data=self.sess_data, csrf=self.csrf)

            category = kwargs.get("category", 4)
            tags = kwargs.get("tags", "")
            summary = kwargs.get("summary", "")
            cover_image_path = kwargs.get("cover_image_path", images[0] if images else None)

            result = api.publish_article(
                title=title,
                content=content,
                category=category,
                tags=tags,
                summary=summary,
                cover_image_path=cover_image_path,
            )

            return PublishResult(
                success=result.get("success", False),
                platform=self.name,
                message=result.get("message", "发布完成"),
                raw_response=result,
            )
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.name,
                message=f"B站API发布失败: {e}",
            )

    def _publish_via_rpa(
        self, title: str, content: str, images: List[str], **kwargs: Any
    ) -> PublishResult:
        """通过RPA浏览器自动化发布B站专栏."""
        try:
            from ..rpa.bilibili_rpa import BilibiliRPA

            with BilibiliRPA() as rpa:
                result = rpa.publish(title=title, content=content, images=images, **kwargs)

            return PublishResult(
                success=result.get("success", False),
                platform=self.name,
                message=result.get("message", "RPA发布完成"),
                raw_response=result,
            )
        except ImportError:
            return PublishResult(
                success=False,
                platform=self.name,
                message="未安装playwright，请运行: pip install playwright && playwright install chromium",
            )
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.name,
                message=f"B站RPA发布失败: {e}",
            )

    def check_login(self) -> bool:
        """检查B站登录状态.

        Returns:
            是否已登录
        """
        if not self.sess_data:
            return False

        try:
            from ..api.bilibili_api import BilibiliAPI
            api = BilibiliAPI(sess_data=self.sess_data, csrf=self.csrf)
            return api.check_login()
        except Exception:
            return False
