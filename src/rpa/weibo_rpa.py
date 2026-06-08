"""微博 RPA 浏览器自动化模块.

使用 Playwright 自动化微博的发布功能。
"""

import os
import time
from typing import Any, Dict, List, Optional

from .base import RPABase


class WeiboRPA(RPABase):
    """微博 RPA 自动化.

    使用示例:
        rpa = WeiboRPA()
        with rpa:
            rpa.login()
            result = rpa.publish(title="标题", content="内容", images=["image1.jpg"])
    """

    PLATFORM = "weibo"
    LOGIN_URL = "https://weibo.com/"
    PUBLISH_URL = "https://weibo.com/"

    def login(self, interactive: bool = True) -> bool:
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
            print(f"[RPA-微博] 登录失败: {e}")
            return False

    def publish(self, title: str, content: str, images: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        if not self._page and not self.launch_browser():
            return {"success": False, "message": "启动浏览器失败"}

        try:
            allow_login_prompt = kwargs.get("allow_login_prompt", self.auto_login)
            if not self.login(interactive=allow_login_prompt):
                return {"success": False, "message": self.login_required_message("微博")}

            print("[RPA-微博] 正在打开微博首页...")
            self._page.goto(self.PUBLISH_URL, wait_until="domcontentloaded")
            self._page.wait_for_load_state("networkidle")
            time.sleep(2)

            # 构建微博文本
            text = f"{title}\n\n{content}" if title else content
            text = text[:2000]

            # 填写内容（微博发布框通常在首页顶部）
            print("[RPA-微博] 填写内容...")
            self._fill_rich_editor(
                self._page,
                [
                    '[node-type="textIpt"]',
                    'textarea[node-type="textIpt"]',
                    'textarea[class*="input"]',
                    '[contenteditable="true"]',
                    'textarea.W_input',
                    '[class*="publish"] textarea',
                ],
                text,
                label="发布框",
            )
            time.sleep(2)

            # 上传图片
            if images:
                print(f"[RPA-微博] 上传 {len(images)} 张图片...")
                valid_images = [p for p in images[:18] if os.path.exists(p)]
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
                    time.sleep(3)

            self.take_screenshot("before_publish")

            # 点击发布
            print("[RPA-微博] 正在发布...")
            clicked = self._click_button(
                self._page,
                [
                    '[node-type="submit"]',
                    'button:has-text("发布")',
                    'a:has-text("发布")',
                    '.publish-btn',
                    '[class*="send"]',
                    '.W_btn_a[action-type="submit"]',
                ],
                label="发布按钮",
            )
            if clicked:
                time.sleep(4)
                self.take_screenshot("after_publish")
                return {
                    "success": True,
                    "message": "微博发布成功（RPA模式）",
                    "url": self._page.url,
                }
            else:
                self.take_screenshot("publish_button_not_found")
                return {"success": False, "message": "未找到发布按钮，请手动发布"}

        except Exception as e:
            self.take_screenshot("error")
            return {"success": False, "message": f"微博RPA发布失败: {e}"}
