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
        super().__init__(platform_name="xiaohongshu", headless=headless, **kwargs)

    def login(self, interactive: bool = True) -> bool:
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

    def publish(self, title: str, content: str, images: list[str], **kwargs) -> dict:
        if not self._page:
            if not self.launch_browser():
                return {"success": False, "message": "启动浏览器失败"}

        try:
            allow_login_prompt = kwargs.get("allow_login_prompt", self.auto_login)
            if not self.login(interactive=allow_login_prompt):
                return {"success": False, "message": self.login_required_message("小红书")}

            print("[RPA-小红书] 正在打开发布页面...")
            self._page.goto(self.PUBLISH_URL, wait_until="domcontentloaded")
            self._page.wait_for_load_state("networkidle")
            time.sleep(2)

            # 小红书必须先上传图片
            if images:
                print(f"[RPA-小红书] 上传 {len(images)} 张图片...")
                self._upload_files(
                    self._page,
                    [
                        'input[type="file"]',
                        '.upload-input',
                        '.image-uploader input',
                        '[class*="upload"] input',
                    ],
                    images,
                    label="图片上传",
                )
                time.sleep(5)  # 图片上传和处理需要较长时间

            # 填写标题
            print(f"[RPA-小红书] 填写标题: {title[:20]}...")
            if not self._fill_input(
                self._page,
                [
                    'input[placeholder*="标题"]',
                    '#title',
                    '.title-input input',
                    '[class*="title"] input',
                    '.note-title input',
                ],
                title[:20],
                label="标题",
            ):
                self._page.keyboard.press("Tab")
                self._page.keyboard.type(title[:20])

            time.sleep(1)

            # 填写内容
            print("[RPA-小红书] 填写内容...")
            self._fill_rich_editor(
                self._page,
                [
                    '[contenteditable="true"]',
                    '[placeholder*="内容"]',
                    '#content',
                    '.content-input',
                    '[class*="content"] [contenteditable]',
                    'div[class*="editor"]',
                ],
                content[:1000],
                label="内容编辑器",
            )
            time.sleep(2)

            self.take_screenshot("before_publish")

            # 点击发布
            print("[RPA-小红书] 正在发布...")
            clicked = self._click_button(
                self._page,
                [
                    'button:has-text("发布")',
                    'button:has-text("发表")',
                    '.publishBtn',
                    '.submit-btn',
                    '[class*="publish"] button',
                ],
                label="发布按钮",
            )
            if clicked:
                time.sleep(5)
                self.take_screenshot("after_publish")
                return {
                    "success": True,
                    "message": "小红书笔记发布成功（RPA模式）",
                    "url": self._page.url,
                }
            else:
                self.take_screenshot("publish_button_not_found")
                return {"success": False, "message": "未找到发布按钮，请手动发布"}

        except Exception as e:
            self.take_screenshot("error")
            return {"success": False, "message": f"小红书RPA发布失败: {e}"}
