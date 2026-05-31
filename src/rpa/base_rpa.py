"""RPA基础模块.

提供浏览器自动化的核心功能：Cookie管理、登录检测、浏览器操作。
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


class LoginTimeoutError(Exception):
    """登录超时异常."""


class BaseRPA:
    """RPA浏览器自动化基类.

    提供Cookie管理、登录检测、浏览器生命周期管理等通用功能。
    子类只需实现 login() 和 publish() 方法。

    使用示例:
        rpa = BilibiliRPA()
        rpa.login()       # 首次弹出浏览器手动登录
        rpa.publish(...)  # 后续自动使用保存的Cookie
        rpa.close()
    """

    # 子类需覆盖
    PLATFORM: str = ""
    LOGIN_URL: str = ""
    HOME_URL: str = ""

    def __init__(self, headless: bool = False) -> None:
        """初始化RPA.

        Args:
            headless: 是否无头模式（后台运行浏览器）
        """
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # Cookie存储路径
        self._cookie_dir = os.path.join(
            os.path.expanduser("~"), ".multi_publisher", "cookies"
        )
        os.makedirs(self._cookie_dir, exist_ok=True)

    @property
    def _cookie_path(self) -> str:
        """Cookie文件路径."""
        return os.path.join(self._cookie_dir, f"{self.PLATFORM}.json")

    def _launch_browser(self) -> None:
        """启动浏览器."""
        if self._browser is not None:
            return

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )

    def _create_context(self) -> BrowserContext:
        """创建浏览器上下文并加载Cookie."""
        self._launch_browser()

        context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        # 加载已保存的Cookie
        cookies = self._load_cookies()
        if cookies:
            context.add_cookies(cookies)

        self._context = context
        return context

    def _new_page(self) -> Page:
        """创建新页面."""
        if self._context is None:
            self._create_context()

        self._page = self._context.new_page()
        return self._page

    def _load_cookies(self) -> List[Dict[str, Any]]:
        """从文件加载Cookie."""
        try:
            if os.path.exists(self._cookie_path):
                with open(self._cookie_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return []

    def _save_cookies(self) -> None:
        """保存当前上下文的Cookie到文件."""
        if self._context is None:
            return

        try:
            cookies = self._context.cookies()
            with open(self._cookie_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[RPA] 保存Cookie失败: {e}")

    def check_login(self) -> bool:
        """检查是否已登录（通过Cookie文件判断）.

        Returns:
            是否有保存的Cookie
        """
        cookies = self._load_cookies()
        if not cookies:
            return False

        # 检查关键Cookie是否过期
        current_time = time.time()
        for cookie in cookies:
            expires = cookie.get("expires", -1)
            if expires > 0 and expires < current_time:
                # 有过期的Cookie，可能需要重新登录
                continue
            # 只要有一个未过期的session Cookie就认为有效
            if cookie.get("httpOnly") or cookie.get("secure"):
                return True

        return len(cookies) > 0

    def login(self, timeout: int = 120) -> bool:
        """打开浏览器等待用户手动登录.

        Args:
            timeout: 等待超时秒数

        Returns:
            是否登录成功

        Raises:
            LoginTimeoutError: 超时未完成登录
        """
        self._create_context()
        page = self._new_page()

        print(f"[RPA] 正在打开 {self.PLATFORM} 登录页面...")
        print(f"[RPA] 请在浏览器中手动完成登录，登录成功后会自动继续")
        page.goto(self.LOGIN_URL, wait_until="domcontentloaded")

        # 等待用户完成登录（URL跳转或特定元素出现）
        try:
            page.wait_for_url(
                f"**/{self.HOME_URL}**",
                timeout=timeout * 1000,
            )
            # 额外等待一下让Cookie完全设置
            time.sleep(2)
            self._save_cookies()
            print(f"[RPA] {self.PLATFORM} 登录成功，Cookie已保存！")
            return True
        except Exception:
            # 尝试通过检查元素判断是否已登录
            try:
                if self._check_login_indicator(page):
                    time.sleep(2)
                    self._save_cookies()
                    print(f"[RPA] {self.PLATFORM} 登录成功，Cookie已保存！")
                    return True
            except Exception:
                pass

            print(f"[RPA] {self.PLATFORM} 登录超时")
            return False

    def _check_login_indicator(self, page: Page) -> bool:
        """检查页面上是否存在登录成功的标志.

        子类可覆盖此方法提供平台特定的检测逻辑。

        Args:
            page: 页面对象

        Returns:
            是否已登录
        """
        return False

    def close(self) -> None:
        """关闭浏览器."""
        try:
            if self._page:
                self._page.close()
            if self._context:
                self._save_cookies()
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    def __del__(self) -> None:
        """析构时关闭浏览器."""
        self.close()

    def __repr__(self) -> str:
        """返回字符串表示."""
        return f"<{self.__class__.__name__}(platform={self.PLATFORM})>"
