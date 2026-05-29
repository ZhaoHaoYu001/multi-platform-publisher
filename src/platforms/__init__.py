"""各平台实现模块."""

from .wechat import WechatPlatform
from .zhihu import ZhihuPlatform

__all__ = ["WechatPlatform", "ZhihuPlatform"]
