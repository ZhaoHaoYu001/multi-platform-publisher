"""微信公众号API模块.

本模块提供了微信公众号的API调用功能。
"""

import json
import os
import time
from typing import Any, Dict, Optional

import requests


class WechatAPI:
    """微信公众号API客户端.

    使用示例:
        api = WechatAPI(app_id="your_app_id", app_secret="your_app_secret")

        # 获取access_token
        token = api.get_access_token()

        # 上传图片
        media_id = api.upload_material("image.jpg", "image")

        # 发布文章
        result = api.publish_article(title="标题", content="<p>内容</p>")
    """

    BASE_URL = "https://api.weixin.qq.com/cgi-bin"

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        token_cache_path: str = ".wechat_token_cache",
    ) -> None:
        """初始化微信API客户端.

        Args:
            app_id: 微信公众号AppID
            app_secret: 微信公众号AppSecret
            token_cache_path: token缓存文件路径
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self._token_cache_path = token_cache_path
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    def get_access_token(self, force_refresh: bool = False) -> str:
        """获取access_token.

        自动缓存token，过期前自动刷新。

        Args:
            force_refresh: 是否强制刷新

        Returns:
            access_token字符串

        Raises:
            ValueError: 获取失败时抛出
        """
        # 检查缓存
        if not force_refresh and self._is_token_valid():
            return self._access_token  # type: ignore

        # 尝试从文件加载
        if not force_refresh and self._load_token_from_cache():
            return self._access_token  # type: ignore

        # 请求新token
        url = f"{self.BASE_URL}/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if "access_token" in data:
                self._access_token = data["access_token"]
                self._token_expires_at = time.time() + data.get("expires_in", 7200) - 300
                self._save_token_to_cache()
                return self._access_token  # type: ignore
            else:
                error_msg = data.get("errmsg", "未知错误")
                error_code = data.get("errcode", -1)
                raise ValueError(f"获取access_token失败: [{error_code}] {error_msg}")

        except requests.RequestException as e:
            raise ValueError(f"网络请求失败: {e}")

    def _is_token_valid(self) -> bool:
        """检查token是否有效."""
        return (
            self._access_token is not None
            and time.time() < self._token_expires_at
        )

    def _load_token_from_cache(self) -> bool:
        """从缓存文件加载token."""
        try:
            if os.path.exists(self._token_cache_path):
                with open(self._token_cache_path, "r") as f:
                    cache = json.load(f)
                    if cache.get("app_id") == self.app_id:
                        self._access_token = cache.get("access_token")
                        self._token_expires_at = cache.get("expires_at", 0)
                        return self._is_token_valid()
        except (json.JSONDecodeError, IOError):
            pass
        return False

    def _save_token_to_cache(self) -> None:
        """保存token到缓存文件."""
        try:
            cache = {
                "app_id": self.app_id,
                "access_token": self._access_token,
                "expires_at": self._token_expires_at,
            }
            with open(self._token_cache_path, "w") as f:
                json.dump(cache, f)
        except IOError:
            pass

    def upload_material(
        self,
        file_path: str,
        media_type: str = "image",
    ) -> str:
        """上传素材.

        Args:
            file_path: 文件路径
            media_type: 素材类型（image/thumb/video/voice）

        Returns:
            media_id

        Raises:
            FileNotFoundError: 文件不存在时抛出
            ValueError: 上传失败时抛出
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        token = self.get_access_token()
        url = f"{self.BASE_URL}/media/upload"
        params = {
            "access_token": token,
            "type": media_type,
        }

        try:
            with open(file_path, "rb") as f:
                files = {"media": (os.path.basename(file_path), f)}
                response = requests.post(url, params=params, files=files, timeout=30)
                data = response.json()

            if "media_id" in data:
                return data["media_id"]
            else:
                error_msg = data.get("errmsg", "未知错误")
                raise ValueError(f"上传素材失败: {error_msg}")

        except requests.RequestException as e:
            raise ValueError(f"网络请求失败: {e}")

    def upload_image_for_content(self, file_path: str) -> str:
        """上传图片用于文章内容.

        Args:
            file_path: 图片文件路径

        Returns:
            图片URL（用于文章中的img标签）
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg"
        params = {"access_token": token}

        try:
            with open(file_path, "rb") as f:
                files = {"media": (os.path.basename(file_path), f)}
                response = requests.post(url, params=params, files=files, timeout=30)
                data = response.json()

            if "url" in data:
                return data["url"]
            else:
                error_msg = data.get("errmsg", "未知错误")
                raise ValueError(f"上传图片失败: {error_msg}")

        except requests.RequestException as e:
            raise ValueError(f"网络请求失败: {e}")

    def create_draft(
        self,
        title: str,
        content: str,
        author: str = "",
        digest: str = "",
        cover_media_id: str = "",
        content_source_url: str = "",
    ) -> str:
        """创建草稿.

        Args:
            title: 文章标题
            content: 文章内容（富文本HTML）
            author: 作者
            digest: 摘要
            cover_media_id: 封面图片media_id
            content_source_url: 原文链接

        Returns:
            media_id（草稿ID）
        """
        token = self.get_access_token()
        url = f"{self.BASE_URL}/draft/add"
        params = {"access_token": token}

        articles = [{
            "title": title,
            "author": author,
            "digest": digest,
            "content": content,
            "content_source_url": content_source_url,
            "thumb_media_id": cover_media_id,
        }]

        try:
            response = requests.post(
                url,
                params=params,
                json={"articles": articles},
                timeout=10,
            )
            data = response.json()

            if "media_id" in data:
                return data["media_id"]
            else:
                error_msg = data.get("errmsg", "未知错误")
                raise ValueError(f"创建草稿失败: {error_msg}")

        except requests.RequestException as e:
            raise ValueError(f"网络请求失败: {e}")

    def publish_article(
        self,
        title: str,
        content: str,
        author: str = "",
        digest: str = "",
        cover_image_path: Optional[str] = None,
        content_source_url: str = "",
    ) -> Dict[str, Any]:
        """发布文章.

        Args:
            title: 文章标题
            content: 文章内容（富文本HTML）
            author: 作者
            digest: 摘要
            cover_image_path: 封面图片路径
            content_source_url: 原文链接

        Returns:
            发布结果字典
        """
        result: Dict[str, Any] = {
            "success": False,
            "message": "",
            "publish_id": None,
        }

        try:
            # 1. 上传封面图片
            cover_media_id = ""
            if cover_image_path:
                cover_media_id = self.upload_material(cover_image_path, "thumb")

            # 2. 创建草稿
            media_id = self.create_draft(
                title=title,
                content=content,
                author=author,
                digest=digest,
                cover_media_id=cover_media_id,
                content_source_url=content_source_url,
            )

            # 3. 发布
            token = self.get_access_token()
            url = f"{self.BASE_URL}/freepublish/submit"
            params = {"access_token": token}

            response = requests.post(
                url,
                params=params,
                json={"media_id": media_id},
                timeout=10,
            )
            data = response.json()

            if "publish_id" in data:
                result["success"] = True
                result["publish_id"] = data["publish_id"]
                result["message"] = "文章已提交发布"
            else:
                error_msg = data.get("errmsg", "未知错误")
                result["message"] = f"发布失败: {error_msg}"

        except Exception as e:
            result["message"] = f"发布异常: {e}"

        return result

    def get_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """获取发布状态.

        Args:
            publish_id: 发布ID

        Returns:
            状态信息
        """
        token = self.get_access_token()
        url = f"{self.BASE_URL}/freepublish/get"
        params = {"access_token": token}

        try:
            response = requests.post(
                url,
                params=params,
                json={"publish_id": publish_id},
                timeout=10,
            )
            return response.json()

        except requests.RequestException as e:
            return {"error": str(e)}
