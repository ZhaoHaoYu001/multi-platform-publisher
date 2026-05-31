"""RPA基类模块.

提供基于Playwright的浏览器自动化基类，各平台RPA实现继承此类。
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Optional


class RPABase(ABC):
    """RPA浏览器自动化基类.

    使用Playwright实现浏览器自动化，支持Cookie持久化和截图保存。

    Attributes:
        platform_name: 平台名称
        headless: 是否无头模式运行
        cookie_file: Cookie文件路径
        screenshot_dir: 截图保存目录
    """

    def __init__(
        self,
        platform_name: str,
        headless: bool = False,
        cookie_dir: str = "cookies",
        screenshot_dir: str = "screenshots",
    ) -> None:
        """初始化RPA基类.

        Args:
            platform_name: 平台名称
            headless: 是否无头模式（默认False，方便用户看到操作）
            cookie_dir: Cookie文件存储目录
            screenshot_dir: 截图保存目录
        """
        self.platform_name = platform_name
        self.headless = headless
        self.cookie_dir = cookie_dir
        self.screenshot_dir = screenshot_dir
        self.cookie_file = os.path.join(cookie_dir, f"{platform_name}_cookies.json")

        # 确保目录存在
        os.makedirs(cookie_dir, exist_ok=True)
        os.makedirs(screenshot_dir, exist_ok=True)

        self._browser = None
        self._context = None
        self._page = None

    def _check_playwright(self) -> bool:
        """检查Playwright是否已安装.

        Returns:
            Playwright是否可用
        """
        try:
            from playwright.sync_api import sync_playwright
            return True
        except ImportError:
            return False

    def launch_browser(self) -> bool:
        """启动浏览器.

        Returns:
            是否成功启动
        """
        if not self._check_playwright():
            return False

        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )

            # 创建上下文
            self._context = self._browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            # 加载已保存的Cookie
            self._load_cookies()

            # 创建页面
            self._page = self._context.new_page()

            return True
        except Exception as e:
            print(f"[RPA] 启动浏览器失败: {e}")
            return False

    def close_browser(self) -> None:
        """关闭浏览器."""
        try:
            if self._context:
                # 保存Cookie
                self._save_cookies()
                self._context.close()
            if self._browser:
                self._browser.close()
            if hasattr(self, '_playwright') and self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        finally:
            self._page = None
            self._context = None
            self._browser = None

    def _load_cookies(self) -> None:
        """从文件加载Cookie."""
        if not os.path.exists(self.cookie_file):
            return

        try:
            import json
            with open(self.cookie_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            if cookies and self._context:
                self._context.add_cookies(cookies)
        except Exception:
            pass

    def _save_cookies(self) -> None:
        """保存Cookie到文件."""
        if not self._context:
            return

        try:
            import json
            cookies = self._context.cookies()
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def take_screenshot(self, name: str = "screenshot") -> str:
        """保存截图.

        Args:
            name: 截图文件名（不含扩展名）

        Returns:
            截图文件路径
        """
        if not self._page:
            return ""

        timestamp = int(time.time())
        filename = f"{self.platform_name}_{name}_{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, filename)

        try:
            self._page.screenshot(path=filepath)
            return filepath
        except Exception:
            return ""

    @abstractmethod
    def login(self) -> bool:
        """执行登录操作.

        子类必须实现此方法。

        Returns:
            登录是否成功
        """
        pass

    @abstractmethod
    def publish(
        self,
        title: str,
        content: str,
        images: list[str],
        **kwargs,
    ) -> dict:
        """执行发布操作.

        子类必须实现此方法。

        Args:
            title: 标题
            content: 内容
            images: 图片路径列表
            **kwargs: 其他参数

        Returns:
            发布结果字典，包含 success, message, url 等字段
        """
        pass

    def __enter__(self):
        """上下文管理器入口."""
        self.launch_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口."""
        self.close_browser()
        return False
