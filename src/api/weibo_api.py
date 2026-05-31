"""微博 API 封装.

提供微博的创建和发布功能。
使用 Cookie 认证方式。
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

import requests


class WeiboAPI:
    """微博 API 封装.

    使用示例:
        api = WeiboAPI(cookie="your_cookie")
        result = api.create_and_publish(
            title="标题",
            content="内容",
            images=["image1.jpg", "image2.jpg"],
        )
    """

    BASE_URL = "https://weibo.com"
    API_URL = "https://weibo.com/ajax"

    def __init__(self, cookie: str = "") -> None:
        """初始化微博 API.

        Args:
            cookie: 微博 Cookie
        """
        self._cookie = cookie
        self._session = requests.Session()
        if cookie:
            self._session.headers["Cookie"] = cookie
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://weibo.com/",
            "X-Requested-With": "XMLHttpRequest",
        })

    def check_login(self) -> bool:
        """检查登录状态.

        Returns:
            是否已登录
        """
        try:
            resp = self._session.get(
                f"{self.API_URL}/feed/friendstimeline",
                timeout=10,
            )
            return resp.status_code == 200 and "ok" in resp.text.lower()
        except Exception:
            return False

    def upload_image(self, image_path: str) -> Optional[str]:
        """上传图片到微博.

        Args:
            image_path: 图片文件路径

        Returns:
            上传后的图片PID，失败返回 None
        """
        if not os.path.exists(image_path):
            return None

        try:
            with open(image_path, "rb") as f:
                files = {"pic": (os.path.basename(image_path), f, "image/jpeg")}
                resp = self._session.post(
                    "https://weibo.com/ajax/statuses/uploadPic",
                    files=files,
                    timeout=30,
                )
                data = resp.json()
                if data.get("ok") == 1:
                    return data.get("data", {}).get("pic_id", "")
        except Exception:
            pass
        return None

    def create_and_publish(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """创建并发布微博.

        Args:
            title: 微博标题（会添加到正文开头）
            content: 微博内容
            images: 图片路径列表

        Returns:
            发布结果，包含 url 等信息

        Raises:
            RuntimeError: 发布失败时抛出
        """
        # 构建微博正文
        text = f"{title}\n\n{content}" if title else content
        text = text[:2000]  # 微博内容限制

        # 上传图片
        pic_ids = []
        if images:
            for img_path in images[:18]:  # 微博最多18张图
                if img_path.startswith("http"):
                    continue
                pid = self.upload_image(img_path)
                if pid:
                    pic_ids.append(pid)

        # 构建发布请求
        payload = {
            "content": text,
        }
        if pic_ids:
            payload["pic_id"] = ",".join(pic_ids)

        try:
            resp = self._session.post(
                f"{self.API_URL}/statuses/update",
                data=payload,
                timeout=30,
            )
            data = resp.json()
            if data.get("ok") == 1:
                post_id = data.get("data", {}).get("id", "")
                return {
                    "success": True,
                    "url": f"https://weibo.com/{post_id}",
                    "post_id": post_id,
                }
            else:
                raise RuntimeError(f"发布失败: {data.get('msg', '未知错误')}")
        except requests.RequestException as e:
            raise RuntimeError(f"API请求失败: {e}")
