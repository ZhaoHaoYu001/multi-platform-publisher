"""抖音 RPA 浏览器自动化模块.

使用 Playwright 自动化抖音创作者平台的图文笔记发布。
"""

import os
import time
from typing import Any, Dict, List, Optional

from .base import RPABase


class DouyinRPA(RPABase):
    """抖音 RPA 自动化.

    使用示例:
        rpa = DouyinRPA()
        with rpa:
            rpa.login()
            result = rpa.publish(title="标题", content="内容", images=["image1.jpg"])
    """

    PLATFORM = "douyin"
    LOGIN_URL = "https://creator.douyin.com/"
    PUBLISH_URL = "https://creator.douyin.com/creator-micro/content/upload"

    def login(self, interactive: bool = True) -> bool:
        if not self._page and not self.launch_browser():
            return False
        try:
            return self.ensure_logged_in(
                url=self.LOGIN_URL,
                cookie_names=["sessionid", "sid_guard"],
                platform_label="抖音",
                timeout=120,
                allow_interactive=interactive,
            )
        except Exception as e:
            print(f"[RPA-抖音] 登录失败: {e}")
            return False

    def publish(self, title: str, content: str, images: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        if not self._page and not self.launch_browser():
            return {"success": False, "message": "启动浏览器失败"}

        try:
            allow_login_prompt = kwargs.get("allow_login_prompt", self.auto_login)
            if not self.login(interactive=allow_login_prompt):
                return {"success": False, "message": self.login_required_message("抖音")}

            print("[RPA-抖音] 正在打开图文发布页面...")
            self._page.goto(self.PUBLISH_URL, wait_until="domcontentloaded")
            self._page.wait_for_load_state("networkidle")
            time.sleep(2)

            # 上传图片（抖音图文需要先传图）
            if images:
                print(f"[RPA-抖音] 上传 {len(images)} 张图片...")
                valid_images = [p for p in images if os.path.exists(p)]
                if valid_images:
                    self._upload_files(
                        self._page,
                        [
                            'input[type="file"]',
                            '.upload-input',
                            '[class*="upload"] input',
                        ],
                        valid_images,
                        label="图片上传",
                    )
                    time.sleep(4)

            # 填写标题
            print(f"[RPA-抖音] 填写标题: {title[:30]}...")
            if not self._fill_input(
                self._page,
                [
                    '[data-testid="title-input"]',
                    '.title-input input',
                    'input[placeholder*="标题"]',
                    '.title input',
                    'input[class*="title"]',
                ],
                title[:30],
                label="标题",
            ):
                self._page.keyboard.press("Tab")
                self._page.keyboard.type(title[:30])

            time.sleep(1)

            # 填写内容
            print("[RPA-抖音] 填写内容...")
            self._fill_rich_editor(
                self._page,
                [
                    '[data-testid="content-input"]',
                    '[contenteditable="true"]',
                    '.content-input textarea',
                    '[placeholder*="内容"]',
                    'textarea',
                ],
                content[:1000],
                label="内容编辑器",
            )
            time.sleep(2)

            self.take_screenshot("before_publish")

            # 点击发布
            print("[RPA-抖音] 正在发布...")
            clicked = self._click_button(
                self._page,
                [
                    'button:has-text("发布")',
                    '[data-testid="publish-btn"]',
                    '.publish-btn',
                    '.submit-btn',
                ],
                label="发布按钮",
            )
            if clicked:
                time.sleep(5)
                self.take_screenshot("after_publish")
                return {
                    "success": True,
                    "message": "抖音图文发布成功（RPA模式）",
                    "url": self._page.url,
                }
            else:
                self.take_screenshot("publish_button_not_found")
                return {"success": False, "message": "未找到发布按钮，请手动发布"}

        except Exception as e:
            self.take_screenshot("error")
            return {"success": False, "message": f"抖音RPA发布失败: {e}"}
