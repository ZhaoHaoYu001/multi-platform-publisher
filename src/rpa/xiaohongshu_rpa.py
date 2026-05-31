"""小红书RPA自动化模块.

使用Playwright实现小红书的浏览器自动化发布。
"""

import time
from typing import Optional

from .base import RPABase


class XiaohongshuRPA(RPABase):
    """小红书RPA自动化实现.

    支持通过浏览器自动化登录小红书并发布笔记。
    """

    HOME_URL = "https://www.xiaohongshu.com"
    PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"

    def __init__(self, headless: bool = False, **kwargs) -> None:
        """初始化小红书RPA.

        Args:
            headless: 是否无头模式
            **kwargs: 其他参数
        """
        super().__init__(platform_name="xiaohongshu", headless=headless, **kwargs)

    def login(self, interactive: bool = True) -> bool:
        """执行小红书登录.

        打开小红书创作者中心，等待用户手动扫码或输入密码登录。

        Returns:
            登录是否成功
        """
        if not self._page:
            if not self.launch_browser():
                return False

        try:
            return self.ensure_logged_in(
                url=self.PUBLISH_URL,
                cookie_names=["web_session"],
                platform_label="小红书",
                allow_interactive=interactive,
            )
        except Exception as e:
            print(f"[RPA-小红书] 登录失败: {e}")
            return False

    def publish(
        self,
        title: str,
        content: str,
        images: list[str],
        **kwargs,
    ) -> dict:
        """通过浏览器自动化发布小红书笔记.

        Args:
            title: 笔记标题
            content: 笔记内容（纯文本格式）
            images: 图片路径列表
            **kwargs: 其他参数（topics）

        Returns:
            发布结果字典
        """
        if not self._page:
            if not self.launch_browser():
                return {"success": False, "message": "启动浏览器失败"}

        try:
            # 检查登录状态。真实发布默认只复用预登录态，避免演示时卡在扫码/验证码。
            allow_login_prompt = kwargs.get("allow_login_prompt", self.auto_login)
            if not self.login(interactive=allow_login_prompt):
                return {"success": False, "message": self.login_required_message("小红书")}

            # 访问发布页面
            print("[RPA-小红书] 正在打开发布页面...")
            self._page.goto(self.PUBLISH_URL, wait_until="domcontentloaded")
            time.sleep(3)

            # 上传图片（小红书必须先上传图片）
            if images:
                print(f"[RPA-小红书] 上传 {len(images)} 张图片...")
                file_input = self._page.locator('input[type="file"]')
                if file_input.count() > 0:
                    for img_path in images:
                        try:
                            file_input.first.set_input_files(img_path)
                            time.sleep(3)
                        except Exception as e:
                            print(f"[RPA-小红书] 图片上传失败: {e}")
                time.sleep(2)

            # 填写标题
            print(f"[RPA-小红书] 填写标题: {title[:20]}...")
            title_input = self._page.locator(
                'input[placeholder*="标题"], #title, .title-input, [class*="title"]'
            )
            if title_input.count() > 0:
                title_input.first.fill(title[:20])
            time.sleep(1)

            # 填写内容
            print("[RPA-小红书] 填写内容...")
            content_editor = self._page.locator(
                'textarea[placeholder*="内容"], #content, .content-input, '
                '[contenteditable="true"], [class*="content"]'
            )
            if content_editor.count() > 0:
                content_editor.first.click()
                for line in content.split('\n'):
                    if line.strip():
                        self._page.keyboard.type(line)
                    self._page.keyboard.press("Enter")
            time.sleep(2)

            # 截图
            self.take_screenshot("before_publish")

            # 点击发布
            print("[RPA-小红书] 正在发布...")
            publish_btn = self._page.locator(
                'button:has-text("发布"), button:has-text("发表"), .publishBtn'
            )
            if publish_btn.count() > 0:
                publish_btn.first.click()
                time.sleep(5)

                self.take_screenshot("after_publish")

                return {
                    "success": True,
                    "message": "小红书笔记发布成功（RPA模式）",
                    "url": self._page.url,
                }
            else:
                return {
                    "success": False,
                    "message": "未找到发布按钮，请手动发布",
                }

        except Exception as e:
            self.take_screenshot("error")
            return {"success": False, "message": f"小红书RPA发布失败: {e}"}
