"""知乎RPA自动化模块.

使用Playwright实现知乎的浏览器自动化发布。
"""

import time
from typing import Optional

from .base import RPABase


class ZhihuRPA(RPABase):
    """知乎RPA自动化实现.

    支持通过浏览器自动化登录知乎并发布文章。
    """

    HOME_URL = "https://www.zhihu.com"
    PUBLISH_URL = "https://zhuanlan.zhihu.com/write"

    def __init__(self, headless: bool = False, **kwargs) -> None:
        super().__init__(platform_name="zhihu", headless=headless, **kwargs)

    def login(self, interactive: bool = True) -> bool:
        if not self._page:
            if not self.launch_browser():
                return False
        try:
            return self.ensure_logged_in(
                url=self.HOME_URL,
                cookie_names=["z_c0"],
                platform_label="知乎",
                allow_interactive=interactive,
            )
        except Exception as e:
            print(f"[RPA-知乎] 登录失败: {e}")
            return False

    def publish(self, title: str, content: str, images: list[str], **kwargs) -> dict:
        if not self._page:
            if not self.launch_browser():
                return {"success": False, "message": "启动浏览器失败"}

        try:
            allow_login_prompt = kwargs.get("allow_login_prompt", self.auto_login)
            if not self.login(interactive=allow_login_prompt):
                return {"success": False, "message": self.login_required_message("知乎")}

            print("[RPA-知乎] 正在打开写文章页面...")
            self._page.goto(self.PUBLISH_URL, wait_until="domcontentloaded")
            self._page.wait_for_load_state("networkidle")
            time.sleep(2)

            # 填写标题
            print(f"[RPA-知乎] 填写标题: {title[:30]}...")
            if not self._fill_input(
                self._page,
                [
                    'textarea[placeholder*="标题"]',
                    '.WriteIndex-titleInput textarea',
                    '.public-DraftStyleDefault-block',
                    '[data-testid="article-title"]',
                    '.title-editor textarea',
                ],
                title,
                label="标题",
            ):
                self._page.keyboard.press("Tab")
                self._page.keyboard.type(title)

            time.sleep(1)

            # 填写内容 - 知乎用 Draft.js / Slate 编辑器
            print("[RPA-知乎] 填写内容...")
            self._fill_rich_editor(
                self._page,
                [
                    '.public-DraftEditor-content',
                    '[contenteditable="true"]',
                    '.WriteIndex-content [contenteditable]',
                    '.rich-editor [contenteditable]',
                ],
                content,
                label="内容编辑器",
            )
            time.sleep(2)

            # 上传图片
            if images:
                print(f"[RPA-知乎] 上传 {len(images)} 张图片...")
                self._upload_files(
                    self._page,
                    ['input[type="file"]'],
                    images,
                    label="图片上传",
                )
                time.sleep(3)

            self.take_screenshot("before_publish")

            # 点击发布
            print("[RPA-知乎] 正在发布...")
            clicked = self._click_button(
                self._page,
                [
                    'button:has-text("发布")',
                    'button:has-text("发表")',
                    '.PublishPanel-triggerButton',
                    '[data-testid="publish-button"]',
                ],
                label="发布按钮",
            )
            if clicked:
                time.sleep(2)
                # 确认发布（知乎通常有两步确认）
                confirm_clicked = self._click_button(
                    self._page,
                    ['button:has-text("确认发布")', 'button:has-text("确定")', '.confirm-btn'],
                    timeout=5000,
                    label="确认发布",
                )
                time.sleep(5)
                self.take_screenshot("after_publish")
                return {
                    "success": True,
                    "message": "知乎文章发布成功（RPA模式）",
                    "url": self._page.url,
                }
            else:
                self.take_screenshot("publish_button_not_found")
                return {"success": False, "message": "未找到发布按钮，请手动发布"}

        except Exception as e:
            self.take_screenshot("error")
            return {"success": False, "message": f"知乎RPA发布失败: {e}"}
