"""B站API模块.

本模块提供了B站（哔哩哔哩）的API调用功能。
"""

import os
import re
from typing import Any, Dict, List, Optional

import requests


class BilibiliAPI:
    """B站API客户端.

    使用示例:
        api = BilibiliAPI(sess_data="your_sess_data", csrf="your_csrf")

        # 发布专栏
        result = api.publish_article(
            title="标题",
            content="# 内容\n\n这是文章",
            category=4,
        )
    """

    BASE_URL = "https://api.bilibili.com"

    def __init__(self, sess_data: str = "", csrf: str = "") -> None:
        """初始化B站API客户端.

        Args:
            sess_data: B站SESSDATA cookie值
            csrf: B站bili_jct CSRF token
        """
        self.sess_data = sess_data
        self.csrf = csrf
        self._session = requests.Session()
        self._session.cookies.set("SESSDATA", sess_data)

    def check_login(self) -> bool:
        """检查登录状态.

        Returns:
            是否已登录
        """
        url = f"{self.BASE_URL}/x/web-interface/nav"

        try:
            response = self._session.get(url, timeout=10)
            data = response.json()
            return data.get("code") == 0 and data.get("data", {}).get("isLogin", False)
        except Exception:
            return False

    def upload_image(self, image_path: str) -> Optional[str]:
        """上传图片.

        Args:
            image_path: 图片文件路径

        Returns:
            图片URL，失败返回None
        """
        if not os.path.exists(image_path):
            return None

        url = f"{self.BASE_URL}/x/article/creative/article/upcover"

        try:
            with open(image_path, "rb") as f:
                files = {"binary": (os.path.basename(image_path), f, "image/jpeg")}
                response = self._session.post(url, files=files, timeout=30)
                data = response.json()

            if data.get("code") == 0:
                return data.get("data", {}).get("url")
        except Exception:
            pass

        return None

    def markdown_to_bbcode(self, markdown_content: str) -> str:
        """将Markdown转换为B站BBCode格式.

        Args:
            markdown_content: Markdown格式内容

        Returns:
            BBCode格式内容
        """
        content = markdown_content

        # 标题转换
        content = re.sub(r'^### (.+)$', r'[h3]\1[/h3]', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'[h2]\1[/h2]', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.+)$', r'[h1]\1[/h1]', content, flags=re.MULTILINE)

        # 粗体和斜体
        content = re.sub(r'\*\*(.+?)\*\*', r'[b]\1[/b]', content)
        content = re.sub(r'\*(.+?)\*', r'[i]\1[/i]', content)

        # 删除线
        content = re.sub(r'~~(.+?)~~', r'[s]\1[/s]', content)

        # 代码块
        content = re.sub(
            r'```(\w+)?\n(.*?)```',
            lambda m: f'[code]{m.group(2)}[/code]',
            content,
            flags=re.DOTALL,
        )

        # 行内代码
        content = re.sub(r'`([^`]+)`', r'[code]\1[/code]', content)

        # 引用
        content = re.sub(r'^> (.+)$', r'[quote]\1[/quote]', content, flags=re.MULTILINE)

        # 图片（必须在链接之前处理，避免 ![alt](url) 被链接正则误匹配）
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'[img]\2[/img]', content)

        # 链接
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[url=\2]\1[/url]', content)

        # 无序列表（合并为单个 [list] 块）
        def _wrap_list(matchobj: re.Match) -> str:
            lines = matchobj.group(0).strip().split("\n")
            items = "\n".join(
                f"[*]{re.sub(r'^- ', '', line)}" for line in lines
            )
            return f"[list]\n{items}\n[/list]"

        content = re.sub(r'(?:^- .+$\n?)+', _wrap_list, content, flags=re.MULTILINE)

        # 分割线
        content = re.sub(r'^---+$', '[hr]', content, flags=re.MULTILINE)

        return content

    def create_article(
        self,
        title: str,
        content: str,
        category: int = 4,
        tags: str = "",
        summary: str = "",
        image_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """创建专栏文章.

        Args:
            title: 文章标题
            content: 文章内容（BBCode格式）
            category: 分类ID（4=游戏, 11=数码, 17=汽车等）
            tags: 标签（逗号分隔）
            summary: 摘要
            image_urls: 封面图片URL列表

        Returns:
            创建结果
        """
        url = f"{self.BASE_URL}/x/article/creative/draft/addupdate"
        params = {"csrf": self.csrf}

        # 构建请求数据
        data = {
            "title": title,
            "content": content,
            "category": category,
            "tid": category,
            "banner_url": "",
            "original": 1,
            "reprint": 0,
            "tags": tags,
            "summary": summary[:200] if summary else content[:200],
            "dynamic_intro": "",
            "image_urls": ",".join(image_urls) if image_urls else "",
            "csrf": self.csrf,
        }

        try:
            response = self._session.post(url, data=data, timeout=30)
            return response.json()
        except Exception as e:
            return {"code": -1, "message": str(e)}

    def submit_article(self, article_id: int) -> Dict[str, Any]:
        """提交发布专栏.

        Args:
            article_id: 文章ID

        Returns:
            发布结果
        """
        url = f"{self.BASE_URL}/x/article/creative/draft/submit"
        data = {
            "aid": article_id,
            "csrf": self.csrf,
        }

        try:
            response = self._session.post(url, data=data, timeout=30)
            return response.json()
        except Exception as e:
            return {"code": -1, "message": str(e)}

    def publish_article(
        self,
        title: str,
        content: str,
        category: int = 4,
        tags: str = "",
        summary: str = "",
        cover_image_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发布专栏文章.

        Args:
            title: 文章标题
            content: 文章内容（Markdown格式，会自动转BBCode）
            category: 分类ID
            tags: 标签（逗号分隔）
            summary: 摘要
            cover_image_path: 封面图片路径

        Returns:
            发布结果
        """
        result: Dict[str, Any] = {
            "success": False,
            "message": "",
            "article_id": None,
        }

        try:
            # 1. 检查登录
            if not self.check_login():
                result["message"] = "未登录或登录已过期"
                return result

            # 2. 转换格式
            bbcode_content = self.markdown_to_bbcode(content)

            # 3. 上传封面图片
            image_urls = []
            if cover_image_path and os.path.exists(cover_image_path):
                img_url = self.upload_image(cover_image_path)
                if img_url:
                    image_urls.append(img_url)

            # 4. 创建文章
            create_result = self.create_article(
                title=title,
                content=bbcode_content,
                category=category,
                tags=tags,
                summary=summary,
                image_urls=image_urls,
            )

            if create_result.get("code") != 0:
                result["message"] = f"创建文章失败: {create_result.get('message', '未知错误')}"
                return result

            article_id = create_result.get("data", {}).get("aid")
            if not article_id:
                result["message"] = "未获取到文章ID"
                return result

            # 5. 提交发布
            submit_result = self.submit_article(article_id)

            if submit_result.get("code") == 0:
                result["success"] = True
                result["article_id"] = article_id
                result["message"] = f"文章发布成功，ID: {article_id}"
            else:
                result["message"] = f"提交发布失败: {submit_result.get('message', '未知错误')}"

        except Exception as e:
            result["message"] = f"发布异常: {e}"

        return result

    def get_article_info(self, article_id: int) -> Dict[str, Any]:
        """获取文章信息.

        Args:
            article_id: 文章ID

        Returns:
            文章信息
        """
        url = f"{self.BASE_URL}/x/article/view"
        params = {"id": article_id}

        try:
            response = self._session.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return {"code": -1, "message": str(e)}
