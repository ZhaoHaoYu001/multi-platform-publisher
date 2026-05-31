"""统一凭证管理.

集中管理各平台的 API 凭证，支持 .env 文件和环境变量两种来源。
"""

import os
from typing import Any, Dict, List, Optional


# 各平台所需凭证键
PLATFORM_CREDENTIAL_KEYS: Dict[str, List[str]] = {
    "wechat": ["app_id", "app_secret"],
    "zhihu": ["username", "password"],
    "bilibili": ["sess_data", "csrf"],
    "xiaohongshu": ["cookie"],
    "douyin": ["cookie"],
    "weibo": ["cookie"],
}

# 环境变量名到凭证键的映射
_ENV_KEY_MAP: Dict[str, Dict[str, str]] = {
    "wechat": {
        "WECHAT_APP_ID": "app_id",
        "WECHAT_APP_SECRET": "app_secret",
    },
    "zhihu": {
        "ZHIHU_USERNAME": "username",
        "ZHIHU_PASSWORD": "password",
    },
    "bilibili": {
        "BILIBILI_SESS_DATA": "sess_data",
        "BILIBILI_CSRF": "csrf",
    },
    "xiaohongshu": {
        "XIAOHONGSHU_COOKIE": "cookie",
    },
    "douyin": {
        "DOUYIN_COOKIE": "cookie",
    },
    "weibo": {
        "WEIBO_COOKIE": "cookie",
    },
}


class CredentialStore:
    """统一凭证管理器.

    使用示例:
        store = CredentialStore()
        store.load_from_env()

        # 获取凭证
        creds = store.get("wechat")
        app_id = store.get_key("wechat", "app_id")

        # 检查凭证完整性
        is_ready = store.is_platform_ready("wechat")

        # 列出所有平台状态
        status = store.get_all_status()
    """

    def __init__(self, env_file: Optional[str] = None) -> None:
        """初始化凭证管理器.

        Args:
            env_file: .env 文件路径，None 时自动查找
        """
        self._credentials: Dict[str, Dict[str, str]] = {}
        self._env_file = env_file
        self._loaded = False

    def load_from_env(self, force: bool = False) -> None:
        """从环境变量加载凭证.

        Args:
            force: 强制重新加载
        """
        if self._loaded and not force:
            return

        # 尝试加载 .env 文件
        try:
            from dotenv import load_dotenv
            if self._env_file:
                load_dotenv(self._env_file)
            else:
                load_dotenv()
        except ImportError:
            pass  # python-dotenv 未安装时跳过

        self._credentials = {}
        for platform, env_map in _ENV_KEY_MAP.items():
            creds = {}
            for env_key, cred_key in env_map.items():
                creds[cred_key] = os.getenv(env_key, "")
            self._credentials[platform] = creds

        self._loaded = True

    def get(self, platform: str) -> Dict[str, str]:
        """获取平台全部凭证.

        Args:
            platform: 平台名称

        Returns:
            凭证字典
        """
        if not self._loaded:
            self.load_from_env()
        return self._credentials.get(platform, {}).copy()

    def get_key(self, platform: str, key: str) -> str:
        """获取单个凭证值.

        Args:
            platform: 平台名称
            key: 凭证键名

        Returns:
            凭证值，不存在时返回空字符串
        """
        if not self._loaded:
            self.load_from_env()
        return self._credentials.get(platform, {}).get(key, "")

    def set(self, platform: str, key: str, value: str) -> None:
        """设置凭证值（运行时）.

        Args:
            platform: 平台名称
            key: 凭证键名
            value: 凭证值
        """
        if not self._loaded:
            self.load_from_env()
        if platform not in self._credentials:
            self._credentials[platform] = {}
        self._credentials[platform][key] = value

    def is_platform_ready(self, platform: str) -> bool:
        """检查平台凭证是否完整.

        Args:
            platform: 平台名称

        Returns:
            凭证是否完整可用
        """
        if not self._loaded:
            self.load_from_env()

        required_keys = PLATFORM_CREDENTIAL_KEYS.get(platform, [])
        if not required_keys:
            return False

        creds = self._credentials.get(platform, {})
        return all(creds.get(k) for k in required_keys)

    def get_platform_status(self, platform: str) -> Dict[str, bool]:
        """获取平台凭证配置状态.

        Args:
            platform: 平台名称

        Returns:
            各凭证键的配置状态
        """
        if not self._loaded:
            self.load_from_env()

        creds = self._credentials.get(platform, {})
        required_keys = PLATFORM_CREDENTIAL_KEYS.get(platform, [])
        return {k: bool(creds.get(k)) for k in required_keys}

    def get_all_status(self) -> Dict[str, Dict[str, bool]]:
        """获取所有平台凭证状态.

        Returns:
            平台名到凭证状态的映射
        """
        if not self._loaded:
            self.load_from_env()

        return {
            platform: self.get_platform_status(platform)
            for platform in PLATFORM_CREDENTIAL_KEYS
        }

    def list_platforms(self) -> List[str]:
        """列出所有已知平台.

        Returns:
            平台名称列表
        """
        return list(PLATFORM_CREDENTIAL_KEYS.keys())

    def list_ready_platforms(self) -> List[str]:
        """列出凭证完整的平台.

        Returns:
            凭证完整的平台名称列表
        """
        return [p for p in self.list_platforms() if self.is_platform_ready(p)]

    def has_any_credentials(self) -> bool:
        """检查是否有任何平台配置了凭证.

        Returns:
            是否有任何凭证
        """
        if not self._loaded:
            self.load_from_env()

        for platform in self._credentials:
            if any(self._credentials[platform].values()):
                return True
        return False

    def clear(self) -> None:
        """清除所有凭证（内存中）."""
        self._credentials.clear()
        self._loaded = False

    def __repr__(self) -> str:
        """返回管理器的字符串表示."""
        ready = len(self.list_ready_platforms()) if self._loaded else 0
        total = len(PLATFORM_CREDENTIAL_KEYS)
        return f"<CredentialStore({ready}/{total} platforms ready)>"
