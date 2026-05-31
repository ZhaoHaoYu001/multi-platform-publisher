"""Platform catalog and construction helpers for the demo application."""

import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .platform_manager import PlatformManager
from ..platforms.bilibili import BilibiliPlatform
from ..platforms.wechat import WechatPlatform
from ..platforms.xiaohongshu import XiaohongshuPlatform
from ..platforms.zhihu import ZhihuPlatform


@dataclass(frozen=True)
class PlatformCatalogItem:
    """Static metadata used by the web UI and architecture docs."""

    name: str
    display_name: str
    summary: str
    style: str
    credential_env: Tuple[str, ...]
    supports_rpa: bool = False


PLATFORM_CATALOG: Dict[str, PlatformCatalogItem] = {
    "wechat": PlatformCatalogItem(
        name="wechat",
        display_name="微信公众号",
        summary="适合长图文、正式表达和图文排版。",
        style="Markdown 转富文本，保留标题层级、引用、代码和段落。",
        credential_env=("WECHAT_APP_ID", "WECHAT_APP_SECRET"),
    ),
    "zhihu": PlatformCatalogItem(
        name="zhihu",
        display_name="知乎",
        summary="适合知识分享、教程和较长问答式文章。",
        style="保留 Markdown 结构，并为代码块补充默认语言标记。",
        credential_env=("ZHIHU_USERNAME", "ZHIHU_PASSWORD"),
        supports_rpa=True,
    ),
    "bilibili": PlatformCatalogItem(
        name="bilibili",
        display_name="B站专栏",
        summary="适合教程、测评和带社区语气的专栏内容。",
        style="标题强化、分割线转换，并适配 B站专栏富文本习惯。",
        credential_env=("BILIBILI_SESS_DATA", "BILIBILI_CSRF"),
        supports_rpa=True,
    ),
    "xiaohongshu": PlatformCatalogItem(
        name="xiaohongshu",
        display_name="小红书",
        summary="适合种草、清单、攻略和短内容分享。",
        style="Markdown 转纯文本，自动加入平台化口吻和话题标签。",
        credential_env=("XIAOHONGSHU_COOKIE",),
        supports_rpa=True,
    ),
}


def load_environment() -> None:
    """Load .env when python-dotenv is available."""

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass


def is_credentials_ready(platform_name: str) -> bool:
    """Return whether all configured credential variables are present."""

    item = PLATFORM_CATALOG.get(platform_name)
    if not item:
        return False
    return all(bool(os.getenv(key, "")) for key in item.credential_env)


def build_platform(platform_name: str):
    """Build one platform instance from environment variables."""

    if platform_name == "wechat":
        return WechatPlatform(
            app_id=os.getenv("WECHAT_APP_ID", ""),
            app_secret=os.getenv("WECHAT_APP_SECRET", ""),
        )
    if platform_name == "zhihu":
        return ZhihuPlatform(
            username=os.getenv("ZHIHU_USERNAME", ""),
            password=os.getenv("ZHIHU_PASSWORD", ""),
        )
    if platform_name == "bilibili":
        return BilibiliPlatform(
            sess_data=os.getenv("BILIBILI_SESS_DATA", ""),
            csrf=os.getenv("BILIBILI_CSRF", ""),
        )
    if platform_name == "xiaohongshu":
        return XiaohongshuPlatform(cookie=os.getenv("XIAOHONGSHU_COOKIE", ""))
    raise KeyError(f"Unknown platform: {platform_name}")


def build_platform_manager(
    platform_names: Iterable[str] = PLATFORM_CATALOG.keys(),
) -> PlatformManager:
    """Build a manager with all requested platform implementations."""

    load_environment()

    manager = PlatformManager()
    for name in platform_names:
        if name not in PLATFORM_CATALOG:
            continue
        manager.register(build_platform(name))
    return manager


def get_platform_catalog() -> List[PlatformCatalogItem]:
    """Return platform metadata in display order."""

    return [PLATFORM_CATALOG[name] for name in PLATFORM_CATALOG]
