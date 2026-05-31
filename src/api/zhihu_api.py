"""知乎API模块.

本模块提供了知乎的API调用功能。
"""

import os
import re
from typing import Any, Dict, List, Optional

import requests


class ZhihuAPI:
    """知乎API客户端.

    使用示例:
        api = ZhihuAPI(username="user", password="pass")

        # 登录
        api.login()

        # 上传图片
        img_url = api.upload_image("image.jpg")

        # 发布文章
        result = api.publish_article(title="标题", content="# 内容")
    """

    BASE_URL = "https://www.zhihu.com"
    API_URL = "https://api.zhihu.com"

    def __init__(self, username: str = "", password: str = "") -> None:
        """初始化知乎API客户端.

        Args:
            username: 知乎用户名（手机号/邮箱）
            password: 知乎密码
        """
        self.username = username
        self.password = password
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.zhihu.com/",
        })

    def check_login(self) -> bool:
        """检查登录状态.

        Returns:
            是否已登录
        """
        url = f"{self.API_URL}/v4/me"

        try:
            response = self._session.get(url, timeout=10)
            data = response.json()
            return data.get("uid", 0) != 0
        except Exception:
            return False

    def login(self) -> bool:
        """执行登录.

        Returns:
            是否登录成功
        """
        if not self.username or not self.password:
            return False

        url = f"{self.BASE_URL}/api/v3/sign_in"

        try:
            # 获取验证码token
            captcha_url = f"{self.BASE_URL}/api/v3/captcha"
            captcha_resp = self._session.get(captcha_url, timeout=10)
            captcha_data = captcha_resp.json() if captcha_resp.ok else {}

            data = {
                "username": self.username,
                "password": self.password,
                "grant_type": "password",
                "source": "com.zhihu.web",
                "captcha": "",
                "lang": "cn",
            }

            response = self._session.post(url, data=data, timeout=10)
            result = response.json()

            return result.get("uid", 0) != 0 or result.get("token")
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

        url = f"{self.API_URL}/v4/upload_images"

        try:
            with open(image_path, "rb") as f:
                files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
                response = self._session.post(url, files=files, timeout=30)
                data = response.json()

            if "src" in data:
                return data["src"]
            # 批量上传格式
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("src")
        except Exception:
            pass

        return None

    def create_article(
        self,
        title: str,
        content: str,
        image_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """创建文章.

        Args:
            title: 文章标题
            content: 文章内容（Markdown/HTML格式）
            image_urls: 图片URL列表

        Returns:
            创建结果
        """
        url = f"{self.API_URL}/v4/articles"

        data = {
            "title": title,
            "content": content,
            "delta_time": 0,
        }

        try:
            response = self._session.post(url, json=data, timeout=30)
            return response.json()
        except Exception as e:
            return {"code": -1, "message": str(e)}

    def publish_article(self, article_id: int) -> Dict[str, Any]:
        """发布文章.

        Args:
            article_id: 文章ID

        Returns:
            发布结果
        """
        url = f"{self.API_URL}/v4/articles/{article_id}/publish"

        try:
            response = self._session.post(url, timeout=30)
            return response.json()
        except Exception as e:
            return {"code": -1, "message": str(e)}

    def create_and_publish(
        self,
        title: str,
        content: str,
        image_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """创建并发布文章.

        Args:
            title: 文章标题
            content: 文章内容
            image_urls: 图片URL列表

        Returns:
            发布结果字典，包含success、message、article_id
        """
        result: Dict[str, Any] = {
            "success": False,
            "message": "",
            "article_id": None,
        }

        try:
            # 1. 检查登录
            if not self.check_login():
                if not self.login():
                    result["message"] = "未登录或登录失败"
                    return result

            # 2. 创建文章
            create_result = self.create_article(
                title=title,
                content=content,
                image_urls=image_urls,
            )

            article_id = create_result.get("id")
            if not article_id:
                result["message"] = (
                    f"创建文章失败: {create_result.get('message', '未知错误')}"
                )
                return result

            # 3. 发布文章
            publish_result = self.publish_article(article_id)

            if publish_result.get("code", 0) == 0 or publish_result.get("id"):
                result["success"] = True
                result["article_id"] = article_id
                result["message"] = f"知乎文章发布成功，ID: {article_id}"
            else:
                result["message"] = (
                    f"发布失败: {publish_result.get('message', '未知错误')}"
                )

        except Exception as e:
            result["message"] = f"发布异常: {e}"

        return result
