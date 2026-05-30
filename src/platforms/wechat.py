"""微信公众号平台实现模块.

本模块提供了微信公众号的内容发布功能。
"""

from typing import Any, Dict, List, Optional

from ..core.platform_base import PlatformBase, PublishResult


class WechatPlatform(PlatformBase):
    """微信公众号平台实现.

    平台特性：
    - 标题限制：64字符
    - 内容类型：富文本（richtext）
    - 图片限制：10张
    - 支持Markdown转换为富文本

    Attributes:
        name: 平台名称，固定为 "wechat"
        max_title_length: 标题最大长度，64字符
        max_images: 最大图片数量，10张
        content_type: 内容类型，richtext
    """

    name: str = "wechat"
    max_title_length: int = 64
    max_content_length: int = 20000
    max_images: int = 10
    content_type: str = "richtext"

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None) -> None:
        """初始化微信公众号平台.

        Args:
            app_id: 微信公众号AppID
            app_secret: 微信公众号AppSecret
        """
        super().__init__()
        self.app_id = app_id
        self.app_secret = app_secret
        self._access_token: Optional[str] = None

    def adapt_content(self, content: str) -> str:
        """适配内容为微信富文本格式.

        将Markdown转换为微信支持的富文本格式。

        Args:
            content: Markdown格式的内容

        Returns:
            微信富文本格式的内容
        """
        # 先调用父类的基础适配
        content = super().adapt_content(content)

        # Markdown转微信富文本
        import re

        # 标题转换
        content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)

        # 粗体和斜体
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)

        # 代码块
        content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)

        # 引用
        content = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', content, flags=re.MULTILINE)

        # 段落（空行分隔）
        content = re.sub(r'\n\n', '</p><p>', content)

        # 包装在p标签中
        content = f'<p>{content}</p>'

        return content

    def _do_publish(
        self,
        title: str,
        content: str,
        images: List[str],
        **kwargs: Any,
    ) -> PublishResult:
        """执行微信公众号发布.

        Args:
            title: 适配后的标题
            content: 适配后的内容（富文本格式）
            images: 图片路径列表
            **kwargs: 其他参数（author, digest, cover_image_path）

        Returns:
            发布结果
        """
        # 检查凭证
        if not self.app_id or not self.app_secret:
            return PublishResult(
                success=True,
                platform=self.name,
                message=(
                    "微信公众号发布需要以下步骤：\n"
                    "1. 配置 access_token\n"
                    "2. 上传封面素材\n"
                    "3. 创建草稿\n"
                    "4. 提交发布\n"
                    "请配置 app_id 和 app_secret 后重试"
                ),
            )

        try:
            from ..api.wechat_api import WechatAPI

            api = WechatAPI(app_id=self.app_id, app_secret=self.app_secret)

            # 获取可选参数
            author = kwargs.get("author", "")
            digest = kwargs.get("digest", "")
            cover_image_path = kwargs.get("cover_image_path", images[0] if images else None)

            result = api.publish_article(
                title=title,
                content=content,
                author=author,
                digest=digest,
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
                message=f"发布失败: {str(e)}",
            )

    def get_access_token(self) -> Optional[str]:
        """获取微信公众号access_token.

        Returns:
            access_token字符串，获取失败返回None
        """
        if not self.app_id or not self.app_secret:
            return None

        try:
            from ..api.wechat_api import WechatAPI
            api = WechatAPI(app_id=self.app_id, app_secret=self.app_secret)
            return api.get_access_token()
        except Exception:
            return None
