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
        auto_login: Optional[bool] = None,
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
            auto_login: 发布时是否允许弹出登录等待流程。默认读取
                MULTI_PUBLISHER_RPA_AUTO_LOGIN，未配置时关闭。
        """
        self.platform_name = platform_name or getattr(self, "PLATFORM", self.__class__.__name__.lower())
        self.headless = headless
        self.cookie_dir = cookie_dir
        self.screenshot_dir = screenshot_dir
        self.cookie_file = os.path.join(cookie_dir, f"{self.platform_name}_cookies.json")
        self.login_timeout = login_timeout
        env_auto_login = os.getenv("MULTI_PUBLISHER_RPA_AUTO_LOGIN", "false").lower()
        self.auto_login = (
            auto_login
            if auto_login is not None
            else env_auto_login in {"1", "true", "yes", "on"}
        )

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

    def has_saved_session(self) -> bool:
        """检查本地是否已有可复用的RPA登录材料."""
        if os.path.exists(self.cookie_file):
            return True

        if not os.path.isdir(self.profile_path):
            return False

        try:
            return any(os.scandir(self.profile_path))
        except OSError:
            return False

    def session_status(self) -> dict:
        """返回设置页可展示的RPA登录态信息."""
        return {
            "platform": self.platform_name,
            "has_saved_session": self.has_saved_session(),
            "profile_path": self.profile_path,
            "cookie_file": self.cookie_file,
            "auto_login": self.auto_login,
        }

    def login_required_message(self, platform_label: str) -> str:
        """生成真实发布缺少登录态时的提示文案."""
        return (
            f"{platform_label} 未检测到可复用登录态。请先到设置页执行 RPA 预登录，"
            "完成扫码/验证码后再发起真实发布；发布流程将直接复用该浏览器 Profile。"
        )

    def ensure_logged_in(
        self,
        url: str,
        cookie_names: Iterable[str],
        platform_label: str,
        timeout: Optional[int] = None,
        allow_interactive: Optional[bool] = None,
    ) -> bool:
        """复用已登录Profile，必要时等待用户首次手动登录.

        Args:
            url: 用于检测登录态的页面。
            cookie_names: 平台登录Cookie名列表。
            platform_label: 用于日志输出的平台中文名。
            timeout: 等待首次登录的秒数。
            allow_interactive: 是否允许打开登录页并等待用户操作。

        Returns:
            是否已经登录。
        """
        if not self._page and not self.launch_browser():
            return False

        if self.has_login_cookies(cookie_names):
            print(f"[RPA-{platform_label}] 已复用本地登录态: {self.profile_path}")
            return True

        interactive = self.auto_login if allow_interactive is None else allow_interactive
        if isinstance(interactive, str):
            interactive = interactive.lower() in {"1", "true", "yes", "on"}
        if not interactive:
            print(f"[RPA-{platform_label}] 未检测到登录态，已跳过发布时登录等待。")
            print(f"[RPA-{platform_label}] 请先在设置页完成 RPA 预登录: {self.profile_path}")
            return False

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

    # ── 页面交互工具方法 ───────────────────────────────────────────

    def _active_page(self, fallback_page=None):
        """获取当前活动页面."""
        if fallback_page:
            return fallback_page
        if self._page:
            return self._page
        if self._context and self._context.pages:
            return self._context.pages[-1]
        return None

    def _wait_for_any(self, page, selectors: list, timeout: int = 15000, label: str = "元素"):
        """等待任一选择器出现，返回第一个匹配的 Locator 或 None."""
        import time as _time
        deadline = _time.time() + timeout / 1000
        while _time.time() < deadline:
            for sel in selectors:
                try:
                    loc = page.locator(sel)
                    if loc.count() > 0:
                        print(f"[RPA-{self.platform_name}] 找到 {label}: {sel}")
                        return loc.first
                except Exception:
                    continue
            _time.sleep(0.5)
        print(f"[RPA-{self.platform_name}] 未找到 {label}，尝试过的选择器: {selectors}")
        return None

    def _fill_input(self, page, selectors: list, text: str, timeout: int = 15000, label: str = "输入框"):
        """等待输入框出现并填入文本."""
        loc = self._wait_for_any(page, selectors, timeout, label)
        if loc is None:
            return False
        try:
            loc.click()
            loc.fill("")
            loc.fill(text)
            print(f"[RPA-{self.platform_name}] {label}已填写 ({len(text)} 字符)")
            return True
        except Exception as e:
            print(f"[RPA-{self.platform_name}] {label}填写失败: {e}")
            return False

    def _fill_rich_editor(self, page, selectors: list, content: str, timeout: int = 15000, label: str = "编辑器"):
        """向 contenteditable / 富文本编辑器填入内容."""
        loc = self._wait_for_any(page, selectors, timeout, label)
        if loc is None:
            return False
        try:
            loc.click()
            page.wait_for_timeout(500)
            # 尝试使用 evaluate 设置内容（适用于 contenteditable/slate/react 编辑器）
            try:
                page.evaluate(
                    """([el, text]) => {
                        el.focus();
                        if (el.getAttribute('contenteditable') !== null || el.isContentEditable) {
                            el.innerHTML = text;
                            el.dispatchEvent(new Event('input', {bubbles: true}));
                        } else {
                            el.value = text;
                            el.dispatchEvent(new Event('input', {bubbles: true}));
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    }""",
                    [loc.element_handle(), content],
                )
                print(f"[RPA-{self.platform_name}] {label}已通过JS填充 ({len(content)} 字符)")
                return True
            except Exception:
                pass
            # 回退: 逐行键盘输入
            print(f"[RPA-{self.platform_name}] JS填充失败，回退键盘输入...")
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip():
                    page.keyboard.type(line)
                if i < len(lines) - 1:
                    page.keyboard.press("Enter")
            return True
        except Exception as e:
            print(f"[RPA-{self.platform_name}] {label}填写失败: {e}")
            return False

    def _click_button(self, page, selectors: list, timeout: int = 10000, label: str = "按钮"):
        """等待按钮出现并点击."""
        loc = self._wait_for_any(page, selectors, timeout, label)
        if loc is None:
            return False
        try:
            loc.click()
            print(f"[RPA-{self.platform_name}] 已点击 {label}")
            return True
        except Exception as e:
            print(f"[RPA-{self.platform_name}] {label}点击失败: {e}")
            # 尝试 JS 点击
            try:
                loc.evaluate("el => el.click()")
                print(f"[RPA-{self.platform_name}] 已通过JS点击 {label}")
                return True
            except Exception:
                return False

    def _upload_files(self, page, selectors: list, file_paths: list, timeout: int = 10000, label: str = "文件上传"):
        """通过文件输入上传文件."""
        import os as _os
        loc = self._wait_for_any(page, selectors, timeout, label)
        if loc is None:
            return False
        valid = [p for p in file_paths if _os.path.exists(p)]
        if not valid:
            print(f"[RPA-{self.platform_name}] 没有有效的文件路径")
            return False
        try:
            loc.set_input_files(valid)
            print(f"[RPA-{self.platform_name}] 已上传 {len(valid)} 个文件")
            return True
        except Exception as e:
            print(f"[RPA-{self.platform_name}] {label}失败: {e}")
            return False

    @abstractmethod
    def login(self, interactive: bool = True) -> bool:
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
