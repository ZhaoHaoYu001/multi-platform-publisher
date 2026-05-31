"""抖音 RPA 浏览器自动化模块.

使用 Playwright 自动化抖音创作者平台的图文笔记发布。
"""

import os
from typing import Any, Dict, List

from .base import RPABase


class DouyinRPA(RPABase):
    """抖音 RPA 自动化.

    使用示例:
        rpa = DouyinRPA()
        with rpa:
            rpa.login()
            result = rpa.publish(
                title="标题",
                content="内容",
                images=["image1.jpg"],
            )
    """

    PLATFORM = "douyin"
    LOGIN_URL = "https://creator.douyin.com/"
    PUBLISH_URL = "https://creator.douyin.com/creator-micro/content/upload"

    def login(self) -> bool:
        """登录抖音创作者平台.

        打开登录页面，等待用户手动扫码登录。

        Returns:
            是否登录成功
        """
        try:
            page = self._context.new_page()
            page.goto(self.LOGIN_URL)

            # 等待用户登录（检测登录成功标志）
            page.wait_for_url("**/creator-micro/**", timeout=120000)
            self._save_cookies()
            page.close()
            return True
        except Exception as e:
            print(f"登录失败: {e}")
            return False

    def publish(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """发布图文笔记.

        Args:
            title: 笔记标题
            content: 笔记内容
            images: 图片路径列表

        Returns:
            发布结果
        """
        try:
            page = self._context.new_page()
            page.goto(self.PUBLISH_URL)

            # 等待页面加载
            page.wait_for_load_state("networkidle")

            # 上传图片
            if images:
                file_input = page.locator('input[type="file"]')
                for img_path in images:
                    if os.path.exists(img_path):
                        file_input.set_input_files(img_path)
                        page.wait_for_timeout(2000)

            # 填写标题
            title_input = page.locator('[data-testid="title-input"], .title-input, input[placeholder*="标题"]')
            if title_input.count() > 0:
                title_input.first.fill(title[:30])

            # 填写内容
            content_input = page.locator('[data-testid="content-input"], .content-input, textarea, [contenteditable="true"]')
            if content_input.count() > 0:
                content_input.first.fill(content[:1000])

            # 截图保存
            self._take_screenshot(page, "douyin_before_publish")

            # 点击发布按钮
            publish_btn = page.locator('button:has-text("发布"), [data-testid="publish-btn"]')
            if publish_btn.count() > 0:
                publish_btn.first.click()
                page.wait_for_timeout(3000)

            self._take_screenshot(page, "douyin_after_publish")
            page.close()

            return {"success": True, "message": "发布成功"}
        except Exception as e:
            return {"success": False, "message": f"发布失败: {e}"}


from typing import Optional
