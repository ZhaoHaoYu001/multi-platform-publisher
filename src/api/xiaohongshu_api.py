"""小红书API模块.

本模块提供了小红书的API调用功能。
"""

import os
from typing import Any, Dict, List, Optional

import requests


class XiaohongshuAPI:
    """小红书API客户端.

    使用示例:
        api = XiaohongshuAPI(cookie="your_cookie")

        # 检查登录
        api.check_login()

        # 上传图片
        img_url = api.upload_image("image.jpg")

        # 发布笔记
        result = api.publish_note(title="标题", content="内容", image_urls=["url"])
    """

    BASE_URL = "https://edith.xiaohongshu.com"
    WEB_URL = "https://www.xiaohongshu.com"

    def __init__(self, cookie: str = "") -> None:
        """初始化小红书API客户端.

        Args:
            cookie: 小红书登录cookie
        """
        self.cookie = cookie
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com",
        })
        if cookie:
            self._session.headers["Cookie"] = cookie

    def check_login(self) -> bool:
        """检查登录状态.

        Returns:
            是否已登录
        """
        if not self.cookie:
            return False

        url = f"{self.WEB_URL}/api/sns/web/v1/login/activate"

        try:
            response = self._session.get(url, timeout=10)
            data = response.json()
            return data.get("success", False) or data.get("code") == 0
        except Exception:
            # 回退：检查cookie中是否包含关键字段
            return "web_session" in self.cookie

    def upload_image(self, image_path: str) -> Optional[str]:
        """上传图片.

        Args:
            image_path: 图片文件路径

        Returns:
            图片URL，失败返回None
        """
        if not os.path.exists(image_path):
            return None

        url = f"{self.BASE_URL}/api/sns/web/v1/upload/photo"

        try:
            with open(image_path, "rb") as f:
                files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
                response = self._session.post(url, files=files, timeout=30)
                data = response.json()

            if data.get("success") or data.get("code") == 0:
                return data.get("data", {}).get("url")
        except Exception:
            pass

        return None

    def publish_note(
        self,
        title: str,
        content: str,
        image_urls: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """发布笔记.

        Args:
            title: 笔记标题
            content: 笔记内容（纯文本）
            image_urls: 图片URL列表
            topics: 话题列表

        Returns:
            发布结果
        """
        url = f"{self.BASE_URL}/api/sns/web/v1/feed"

        # 构建图片列表
        image_list = []
        if image_urls:
            for i, img_url in enumerate(image_urls):
                image_list.append({
                    "url": img_url,
                    "width": 1080,
                    "height": 1440,
                    "trace_id": f"img_{i}",
                })

        # 构建话题
        topic_list = []
        if topics:
            for topic in topics:
                topic_list.append({"id": topic, "name": topic})

        data = {
            "common": {
                "type": "normal",
                "title": title,
                "note_id": "",
            },
            "image_list": image_list,
            "content": content,
            "topics": topic_list,
        }

        try:
            response = self._session.post(url, json=data, timeout=30)
            return response.json()
        except Exception as e:
            return {"code": -1, "message": str(e)}

    def create_and_publish(
        self,
        title: str,
        content: str,
        image_urls: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """创建并发布笔记.

        Args:
            title: 笔记标题
            content: 笔记内容
            image_urls: 图片URL列表
            topics: 话题列表

        Returns:
            发布结果字典，包含success、message、note_id
        """
        result: Dict[str, Any] = {
            "success": False,
            "message": "",
            "note_id": None,
        }

        try:
            # 1. 检查登录
            if not self.check_login():
                result["message"] = "未登录或cookie已过期"
                return result

            # 2. 发布笔记
            publish_result = self.publish_note(
                title=title,
                content=content,
                image_urls=image_urls,
                topics=topics,
            )

            if publish_result.get("success") or publish_result.get("code") == 0:
                note_id = publish_result.get("data", {}).get("note_id", "")
                result["success"] = True
                result["note_id"] = note_id
                result["message"] = f"小红书笔记发布成功"
            else:
                result["message"] = (
                    f"发布失败: {publish_result.get('message', '未知错误')}"
                )

        except Exception as e:
            result["message"] = f"发布异常: {e}"

        return result
