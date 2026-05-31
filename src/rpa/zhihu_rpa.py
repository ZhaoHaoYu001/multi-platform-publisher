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
        """初始化知乎RPA.

        Args:
            headless: 是否无头模式
            **kwargs: 其他参数
        """
        super().__init__(platform_name="zhihu", headless=headless, **kwargs)

    def login(self) -> bool:
        """执行知乎登录.

        打开知乎首页，等待用户手动扫码或输入密码登录。

        Returns:
            登录是否成功
        """
        if not self._page:
            if not self.launch_browser():
                return False

        try:
            # 访问知乎
            self._page.goto(self.HOME_URL, wait_until="domcontentloaded")
            time.sleep(2)

            # 检查是否已登录
            cookies = self._context.cookies() if self._context else []
            has_token = any(c["name"] == "z_c0" for c in cookies)

            if has_token:
                print("[RPA-知乎] 已检测到登录状态")
                return True

            # 未登录，等待用户手动登录
            print("[RPA-知乎] 请在浏览器中手动登录知乎...")
            print("[RPA-知乎] 登录完成后请按回车继续...")

            # 等待登录完成（最多5分钟）
            for _ in range(300):
                time.sleep(1)
                cookies = self._context.cookies() if self._context else []
                if any(c["name"] == "z_c0" for c in cookies):
                    print("[RPA-知乎] 登录成功！")
                    self._save_cookies()
                    return True

            print("[RPA-知乎] 登录超时")
            return False

        except Exception as e:
            print(f"[RPA-知乎] 登录失败: {e}")
            return False

    def publish(
        self,
        title: str,
        content: str,
        images: list[str],
        **kwargs,
    ) -> dict:
        """通过浏览器自动化发布知乎文章.

        Args:
            title: 文章标题
            content: 文章内容（Markdown格式）
            images: 图片路径列表
            **kwargs: 其他参数

        Returns:
            发布结果字典
        """
        if not self._page:
            if not self.launch_browser():
                return {"success": False, "message": "启动浏览器失败"}

        try:
            # 检查登录状态
            if not self.login():
                return {"success": False, "message": "未登录知乎"}

            # 访问写文章页面
            print("[RPA-知乎] 正在打开写文章页面...")
            self._page.goto(self.PUBLISH_URL, wait_until="domcontentloaded")
            time.sleep(3)

            # 填写标题
            print(f"[RPA-知乎] 填写标题: {title[:30]}...")
            title_input = self._page.locator(
                'textarea[placeholder*="标题"], .WriteIndex-titleInput, #title'
            )
            if title_input.count() > 0:
                title_input.first.fill(title)
            else:
                self._page.keyboard.type(title)

            time.sleep(1)

            # 填写内容
            print("[RPA-知乎] 填写内容...")
            content_editor = self._page.locator(
                '.public-DraftEditor-content, .WriteIndex-content, [contenteditable="true"]'
            )
            if content_editor.count() > 0:
                content_editor.first.click()
                for line in content.split('\n'):
                    if line.strip():
                        self._page.keyboard.type(line)
                    self._page.keyboard.press("Enter")
            time.sleep(2)

            # 上传图片
            if images:
                print(f"[RPA-知乎] 上传 {len(images)} 张图片...")
                file_input = self._page.locator('input[type="file"]')
                if file_input.count() > 0:
                    for img_path in images:
                        try:
                            file_input.first.set_input_files(img_path)
                            time.sleep(2)
                        except Exception as e:
                            print(f"[RPA-知乎] 图片上传失败: {e}")

            # 截图
            self.take_screenshot("before_publish")

            # 点击发布
            print("[RPA-知乎] 正在发布...")
            publish_btn = self._page.locator(
                'button:has-text("发布"), button:has-text("发表"), .PublishPanel-triggerButton'
            )
            if publish_btn.count() > 0:
                publish_btn.first.click()
                time.sleep(3)

                # 确认发布
                confirm_btn = self._page.locator(
                    'button:has-text("确认发布"), button:has-text("确定")'
                )
                if confirm_btn.count() > 0:
                    confirm_btn.first.click()
                    time.sleep(5)

                self.take_screenshot("after_publish")

                return {
                    "success": True,
                    "message": "知乎文章发布成功（RPA模式）",
                    "url": self._page.url,
                }
            else:
                return {
                    "success": False,
                    "message": "未找到发布按钮，请手动发布",
                }

        except Exception as e:
            self.take_screenshot("error")
            return {"success": False, "message": f"知乎RPA发布失败: {e}"}
