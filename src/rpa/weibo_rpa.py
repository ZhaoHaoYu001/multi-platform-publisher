"""微博 RPA 浏览器自动化模块.

使用 Playwright 自动化微博的发布功能。
"""

import os
from typing import Any, Dict, List, Optional

from .base import RPABase


class WeiboRPA(RPABase):
    """微博 RPA 自动化.

    使用示例:
        rpa = WeiboRPA()
        with rpa:
            rpa.login()
            result = rpa.publish(
                title="标题",
                content="内容",
                images=["image1.jpg"],
            )
    """

    PLATFORM = "weibo"
    LOGIN_URL = "https://weibo.com/"
    PUBLISH_URL = "https://weibo.com/"

    def login(self, interactive: bool = True) -> bool:
        """登录微博.

        打开登录页面，等待用户手动登录。

        Returns:
            是否登录成功
        """
        if not self._page and not self.launch_browser():
            return False

        try:
            return self.ensure_logged_in(
                url=self.LOGIN_URL,
                cookie_names=["SUB"],
                platform_label="微博",
                timeout=120,
                allow_interactive=interactive,
            )
        except Exception as e:
            print(f"登录失败: {e}")
            return False

    def publish(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """发布微博.

        Args:
            title: 微博标题
            content: 微博内容
            images: 图片路径列表

        Returns:
            发布结果
        """
        if not self._context and not self.launch_browser():
            return {"success": False, "message": "启动浏览器失败"}

        try:
            allow_login_prompt = kwargs.get("allow_login_prompt", self.auto_login)
            if not self.login(interactive=allow_login_prompt):
                return {"success": False, "message": self.login_required_message("微博")}

            page = self._context.new_page()
            page.goto(self.PUBLISH_URL)
            page.wait_for_load_state("networkidle")

            # 构建微博文本
            text = f"{title}\n\n{content}" if title else content

            # 填写内容
            editor = page.locator('[node-type="textIpt"], textarea, [contenteditable="true"]')
            if editor.count() > 0:
                editor.first.fill(text[:2000])

            # 上传图片
            if images:
                file_input = page.locator('input[type="file"]')
                for img_path in images[:18]:
                    if os.path.exists(img_path):
                        file_input.set_input_files(img_path)
                        page.wait_for_timeout(1500)

            # 截图保存
            self._take_screenshot(page, "weibo_before_publish")

            # 点击发布按钮
            publish_btn = page.locator('[node-type="submit"], button:has-text("发布"), a:has-text("发布")')
            if publish_btn.count() > 0:
                publish_btn.first.click()
                page.wait_for_timeout(3000)

            self._take_screenshot(page, "weibo_after_publish")
            page.close()

            return {"success": True, "message": "发布成功"}
        except Exception as e:
            return {"success": False, "message": f"发布失败: {e}"}
