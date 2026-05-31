"""RPA基类模块.

提供基于Playwright的浏览器自动化基类，各平台RPA实现继承此类。
"""

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Iterable, Optional


class RPABase(ABC):
    """RPA浏览器自动化基类.

    使用Playwright实现浏览器自动化，支持浏览器Profile、Cookie持久化和截图保存。

    Attributes:
        platform_name: 平台名称
        headless: 是否无头模式运行
        cookie_file: Cookie文件路径
        profile_path: 持久化浏览器Profile路径
        screenshot_dir: 截图保存目录
    """

    def __init__(
        self,
        platform_name: Optional[str] = None,
        headless: bool = False,
        cookie_dir: str = "cookies",
        screenshot_dir: str = "screenshots",
        profile_dir: Optional[str] = None,
        use_persistent_profile: bool = True,
        login_timeout: int = 300,
    ) -> None:
        """初始化RPA基类.

        Args:
            platform_name: 平台名称。不传时使用子类 PLATFORM 属性。
            headless: 是否无头模式（默认False，方便用户看到操作）
            cookie_dir: Cookie文件存储目录
            screenshot_dir: 截图保存目录
            profile_dir: 浏览器Profile根目录。默认读取
                MULTI_PUBLISHER_RPA_PROFILE_DIR，未配置时使用用户目录。
            use_persistent_profile: 是否复用持久化浏览器Profile。
            login_timeout: 等待用户首次登录的秒数。
        """
        self.platform_name = platform_name or getattr(self, "PLATFORM", self.__class__.__name__.lower())
        self.headless = headless
        self.cookie_dir = cookie_dir
        self.screenshot_dir = screenshot_dir
        self.cookie_file = os.path.join(cookie_dir, f"{self.platform_name}_cookies.json")
        self.login_timeout = login_timeout

        env_persist = os.getenv("MULTI_PUBLISHER_RPA_PERSIST_PROFILE", "true").lower()
        self.use_persistent_profile = use_persistent_profile and env_persist not in {
            "0",
            "false",
            "no",
            "off",
        }
        profile_root = (
            profile_dir
            or os.getenv("MULTI_PUBLISHER_RPA_PROFILE_DIR")
            or os.path.join(os.path.expanduser("~"), ".multi_publisher", "browser_profiles")
        )
        self.profile_dir = os.path.abspath(os.path.expanduser(profile_root))
        self.profile_path = os.path.join(self.profile_dir, self.platform_name)

        # 确保目录存在
        os.makedirs(cookie_dir, exist_ok=True)
        os.makedirs(screenshot_dir, exist_ok=True)
        os.makedirs(self.profile_path, exist_ok=True)

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
        if self._context and self._page:
            return True

        if not self._check_playwright():
            return False

        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()

            context_options = {
                "viewport": {"width": 1280, "height": 800},
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            }
            launch_args = ["--disable-blink-features=AutomationControlled"]

            if self.use_persistent_profile:
                # 持久化Profile会保存Cookie、localStorage、IndexedDB等完整登录态。
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=self.profile_path,
                    headless=self.headless,
                    args=launch_args,
                    **context_options,
                )
                self._browser = self._context.browser
            else:
                self._browser = self._playwright.chromium.launch(
                    headless=self.headless,
                    args=launch_args,
                )
                self._context = self._browser.new_context(**context_options)

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
            cookies = self._context.cookies()
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def has_login_cookies(self, cookie_names: Iterable[str]) -> bool:
        """检查当前浏览器上下文是否包含平台登录Cookie."""
        if not self._context:
            return False

        expected = set(cookie_names)
        try:
            cookies = self._context.cookies()
        except Exception:
            return False
        return any(cookie.get("name") in expected for cookie in cookies)

    def ensure_logged_in(
        self,
        url: str,
        cookie_names: Iterable[str],
        platform_label: str,
        timeout: Optional[int] = None,
    ) -> bool:
        """复用已登录Profile，必要时等待用户首次手动登录.

        Args:
            url: 用于检测登录态的页面。
            cookie_names: 平台登录Cookie名列表。
            platform_label: 用于日志输出的平台中文名。
            timeout: 等待首次登录的秒数。

        Returns:
            是否已经登录。
        """
        if not self._page and not self.launch_browser():
            return False

        if self.has_login_cookies(cookie_names):
            print(f"[RPA-{platform_label}] 已复用本地登录态: {self.profile_path}")
            return True

        try:
            self._page.goto(url, wait_until="domcontentloaded")
            time.sleep(2)
        except Exception as e:
            print(f"[RPA-{platform_label}] 打开登录检测页失败: {e}")

        if self.has_login_cookies(cookie_names):
            self._save_cookies()
            print(f"[RPA-{platform_label}] 已检测到登录状态")
            return True

        wait_seconds = timeout if timeout is not None else self.login_timeout
        print(f"[RPA-{platform_label}] 未检测到登录态，请在打开的浏览器中登录。")
        print(f"[RPA-{platform_label}] 登录会保存到: {self.profile_path}")

        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            time.sleep(1)
            if self.has_login_cookies(cookie_names):
                self._save_cookies()
                print(f"[RPA-{platform_label}] 登录成功，后续将自动复用该Profile")
                return True

        print(f"[RPA-{platform_label}] 登录超时")
        return False

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

    def _take_screenshot(self, page, name: str = "screenshot") -> str:
        """兼容需要传入页面对象的RPA实现."""
        timestamp = int(time.time())
        filename = f"{self.platform_name}_{name}_{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, filename)
        try:
            page.screenshot(path=filepath)
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
