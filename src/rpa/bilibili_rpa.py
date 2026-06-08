"""B站RPA自动化模块.

使用Playwright实现B站专栏的浏览器自动化发布。
"""

import time
from typing import Optional

from .base import RPABase


class BilibiliRPA(RPABase):
    """B站RPA自动化实现.

    支持通过浏览器自动化登录B站并发布专栏文章。
    """

    HOME_URL = "https://www.bilibili.com"
    ARTICLE_URL = "https://member.bilibili.com/platform/upload/text/edit"

    def __init__(self, headless: bool = False, **kwargs) -> None:
        super().__init__(platform_name="bilibili", headless=headless, **kwargs)

    def login(self, interactive: bool = True) -> bool:
        if not self._page:
            if not self.launch_browser():
                return False
        try:
            return self.ensure_logged_in(
                url=self.HOME_URL,
                cookie_names=["SESSDATA"],
                platform_label="B站",
                allow_interactive=interactive,
            )
        except Exception as e:
            print(f"[RPA-B站] 登录失败: {e}")
            return False

    def publish(self, title: str, content: str, images: list[str], **kwargs) -> dict:
        if not self._page:
            if not self.launch_browser():
                return {"success": False, "message": "启动浏览器失败"}

        try:
            allow_login_prompt = kwargs.get("allow_login_prompt", self.auto_login)
            if not self.login(interactive=allow_login_prompt):
                return {"success": False, "message": self.login_required_message("B站")}

            print("[RPA-B站] 正在打开专栏编辑页面...")
            self._page.goto(self.ARTICLE_URL, wait_until="domcontentloaded")
            self._page.wait_for_load_state("networkidle")
            time.sleep(2)

            # 上传封面图片
            if images:
                print(f"[RPA-B站] 上传封面图片...")
                self._upload_files(
                    self._page,
                    ['input[type="file"]', '.upload-input', '.cover-upload input'],
                    [images[0]],
                    label="封面上传",
                )
                time.sleep(3)

            # 填写标题
            print(f"[RPA-B站] 填写标题: {title[:30]}...")
            if not self._fill_input(
                self._page,
                ['input[placeholder*="标题"]', '.title-input input', '#title', 'input.title', '.title input'],
                title,
                label="标题",
            ):
                # 终极回退: 聚焦并键盘输入
                self._page.keyboard.press("Tab")
                self._page.keyboard.type(title)

            time.sleep(1)

            # 填写内容 - B站用的是 Quill 富文本编辑器
            print("[RPA-B站] 填写内容...")
            html_content = content.replace("\n", "<br>").replace("\n\n", "<br><br>")
            self._fill_rich_editor(
                self._page,
                ['.ql-editor', '[contenteditable="true"]', '.editor-content', '.article-content'],
                html_content,
                label="内容编辑器",
            )
            time.sleep(2)

            # 上传文中图片（如果有更多图片）
            if len(images) > 1:
                self._upload_files(
                    self._page,
                    ['input[type="file"]'],
                    images[1:],
                    label="文中图片",
                )
                time.sleep(3)

            self.take_screenshot("before_publish")

            # 点击发布
            print("[RPA-B站] 正在发布...")
            clicked = self._click_button(
                self._page,
                ['button:has-text("发布")', 'button:has-text("提交")', '.submit-btn', '.publish-btn'],
                label="发布按钮",
            )
            if clicked:
                time.sleep(5)
                self.take_screenshot("after_publish")
                return {
                    "success": True,
                    "message": "B站专栏发布成功（RPA模式）",
                    "url": self._page.url,
                }
            else:
                self.take_screenshot("publish_button_not_found")
                return {"success": False, "message": "未找到发布按钮，请手动发布"}

        except Exception as e:
            self.take_screenshot("error")
            return {"success": False, "message": f"B站RPA发布失败: {e}"}
