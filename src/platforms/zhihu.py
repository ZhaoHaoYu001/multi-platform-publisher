"""知乎平台实现模块.

本模块提供了知乎的内容发布功能。
"""

from typing import Any, List

from ..core.platform_base import PlatformBase, PublishResult


class ZhihuPlatform(PlatformBase):
    """知乎平台实现.

    平台特性：
    - 标题限制：60字符
    - 内容限制：20000字符
    - 内容类型：markdown
    - 图片限制：30张

    Attributes:
        name: 平台名称，固定为 "zhihu"
        max_title_length: 标题最大长度，60字符
        max_content_length: 内容最大长度，20000字符
        max_images: 最大图片数量，30张
        content_type: 内容类型，markdown
    """

    name: str = "zhihu"
    max_title_length: int = 60
    max_content_length: int = 20000
    max_images: int = 30
    content_type: str = "markdown"

    def __init__(self, username: str = "", password: str = "") -> None:
        """初始化知乎平台.

        Args:
            username: 知乎用户名
            password: 知乎密码
        """
        super().__init__()
        self.username = username
        self.password = password

    def adapt_content(self, content: str) -> str:
        """适配内容为知乎Markdown格式.

        知乎原生支持Markdown，无需特殊转换，
        但需要确保格式符合知乎规范。

        Args:
            content: Markdown格式的内容

        Returns:
            适配后的知乎Markdown内容
        """
        # 先调用父类的基础适配
        content = super().adapt_content(content)

        # 知乎特殊处理：
        # 1. 确保代码块有语言标注
        # 2. 处理图片链接
        # 3. 移除知乎不支持的语法

        import re

        # 为没有语言标注的代码块添加默认标注
        content = re.sub(r'```\n', '```text\n', content)

        # 知乎支持的Markdown语法已很完整，无需大幅转换
        return content

    def _do_publish(
        self,
        title: str,
        content: str,
        images: List[str],
        **kwargs: Any,
    ) -> PublishResult:
        """执行知乎发布.

        有API凭证时走API发布，无凭证时降级到RPA浏览器自动化发布。

        Args:
            title: 适配后的标题
            content: 适配后的内容（Markdown格式）
            images: 图片路径列表
            **kwargs: 其他参数

        Returns:
            发布结果
        """
        # 有凭证走API
        if self.username and self.password:
            return self._publish_via_api(title, content, images, **kwargs)

        # 无凭证走RPA
        return self._publish_via_rpa(title, content, images, **kwargs)

    def _publish_via_api(
        self, title: str, content: str, images: List[str], **kwargs: Any
    ) -> PublishResult:
        """通过API发布知乎文章."""
        try:
            from ..api.zhihu_api import ZhihuAPI

            api = ZhihuAPI(username=self.username, password=self.password)

            image_urls = []
            for img_path in images:
                url = api.upload_image(img_path)
                if url:
                    image_urls.append(url)

            result = api.create_and_publish(
                title=title,
                content=content,
                image_urls=image_urls,
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
                message=f"知乎API发布失败: {e}",
            )

    def _publish_via_rpa(
        self, title: str, content: str, images: List[str], **kwargs: Any
    ) -> PublishResult:
        """通过RPA浏览器自动化发布知乎文章."""
        try:
            from ..rpa.zhihu_rpa import ZhihuRPA

            with ZhihuRPA() as rpa:
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
                message=f"知乎RPA发布失败: {e}",
            )

    def check_login(self) -> bool:
        """检查知乎登录状态.

        Returns:
            是否已登录
        """
        if not self.username or not self.password:
            return False

        try:
            from ..api.zhihu_api import ZhihuAPI

            api = ZhihuAPI(username=self.username, password=self.password)
            return api.check_login()
        except Exception:
            return False

    def login(self) -> bool:
        """知乎登录.

        使用用户名密码执行登录操作。

        Returns:
            登录是否成功
        """
        if not self.username or not self.password:
            return False

        try:
            from ..api.zhihu_api import ZhihuAPI

            api = ZhihuAPI(username=self.username, password=self.password)
            return api.login()
        except Exception:
            return False
