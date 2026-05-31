"""抖音开放平台 API 封装.

提供抖音图文笔记的创建和发布功能。
使用 Cookie 认证方式。
"""

import json
import os
from typing import Any, Dict, List, Optional

import requests


class DouyinAPI:
    """抖音 API 封装.

    使用示例:
        api = DouyinAPI(cookie="your_cookie")
        result = api.create_and_publish(
            title="标题",
            content="内容",
            images=["image1.jpg", "image2.jpg"],
        )
    """

    BASE_URL = "https://creator.douyin.com"
    API_URL = "https://creator.douyin.com/web/api"

    def __init__(self, cookie: str = "") -> None:
        """初始化抖音 API.

        Args:
            cookie: 抖音创作者平台 Cookie
        """
        self._cookie = cookie
        self._session = requests.Session()
        if cookie:
            self._session.headers["Cookie"] = cookie
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://creator.douyin.com/",
        })

    def check_login(self) -> bool:
        """检查登录状态.

        Returns:
            是否已登录
        """
        try:
            resp = self._session.get(
                f"{self.API_URL}/user/info/",
                timeout=10,
            )
            data = resp.json()
            return data.get("status_code") == 0
        except Exception:
            return False

    def upload_image(self, image_path: str) -> Optional[str]:
        """上传图片到抖音.

        Args:
            image_path: 图片文件路径

        Returns:
            上传后的图片URL，失败返回 None
        """
        if not os.path.exists(image_path):
            return None

        try:
            with open(image_path, "rb") as f:
                files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
                resp = self._session.post(
                    f"{self.API_URL}/upload/image/",
                    files=files,
                    timeout=30,
                )
                data = resp.json()
                if data.get("status_code") == 0:
                    return data.get("data", {}).get("url")
        except Exception:
            pass
        return None

    def create_and_publish(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """创建并发布图文笔记.

        Args:
            title: 笔记标题
            content: 笔记内容
            images: 图片路径列表

        Returns:
            发布结果，包含 url 等信息

        Raises:
            RuntimeError: 发布失败时抛出
        """
        # 上传图片
        image_urls = []
        if images:
            for img_path in images:
                if img_path.startswith("http"):
                    image_urls.append(img_path)
                else:
                    url = self.upload_image(img_path)
                    if url:
                        image_urls.append(url)

        # 构建发布请求
        payload = {
            "title": title[:30],  # 抖音标题限制30字
            "content": content[:1000],  # 内容限制1000字
            "images": image_urls,
        }

        try:
            resp = self._session.post(
                f"{self.API_URL}/post/create/",
                json=payload,
                timeout=30,
            )
            data = resp.json()
            if data.get("status_code") == 0:
                return {
                    "success": True,
                    "url": data.get("data", {}).get("url", ""),
                    "post_id": data.get("data", {}).get("post_id", ""),
                }
            else:
                raise RuntimeError(f"发布失败: {data.get('status_msg', '未知错误')}")
        except requests.RequestException as e:
            raise RuntimeError(f"API请求失败: {e}")
