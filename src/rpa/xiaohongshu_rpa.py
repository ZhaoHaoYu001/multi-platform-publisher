"""小红书RPA浏览器自动化模块."""

import os
import time
from typing import Any, Dict, List, Optional

from .base_rpa import BaseRPA


class XiaohongshuRPA(BaseRPA):
    """小红书RPA自动化发布.

    流程:
    1. 登录（手动/Cookie自动）
    2. 打开创作者发布页
    3. 上传图片
    4. 填写标题和正文
    5. 发布
    """

    PLATFORM = "xiaohongshu"
    LOGIN_URL = "https://www.xiaohongshu.com"
    HOME_URL = "www.xiaohongshu.com"

    def _check_login_indicator(self, page) -> bool:
        """检查小红书登录状态."""
        try:
            page.wait_for_selector(
                ".user-avatar, .header-avatar, [class*='avatar']",
                timeout=3000,
            )
            return True
        except Exception:
            return False

    def publish(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """发布小红书笔记.

        Args:
            title: 笔记标题（最多20字）
            content: 笔记正文（纯文本）
            images: 图片路径列表（最多9张）
            tags: 话题标签列表

        Returns:
            发布结果字典
        """
        result: Dict[str, Any] = {
            "success": False,
            "message": "",
        }

        try:
            # 检查登录
            if not self.check_login():
                if not self.login():
                    result["message"] = "未登录或登录失败"
                    return result

            page = self._new_page()

            # 打开创作者发布页面
            print("[RPA] 正在打开小红书创作者发布页...")
            page.goto(
                "https://creator.xiaohongshu.com/publish/publish",
                wait_until="domcontentloaded",
            )
            time.sleep(3)

            # 检查登录状态
            if "login" in page.url.lower():
                self._context.close()
                self._create_context()
                page = self._new_page()
                if not self.login():
                    result["message"] = "重新登录失败"
                    return result
                page.goto(
                    "https://creator.xiaohongshu.com/publish/publish",
                    wait_until="domcontentloaded",
                )
                time.sleep(3)

            # 确保在"上传图文"模式
            try:
                tab = page.locator('text="上传图文"').first
                tab.click()
                time.sleep(1)
            except Exception:
                pass

            # 上传图片
            if images:
                print(f"[RPA] 正在上传 {len(images)} 张图片...")
                for img_path in images[:9]:  # 小红书最多9张
                    if os.path.exists(img_path):
                        try:
                            upload_input = page.locator(
                                'input[type="file"][accept*="image"]'
                            ).first
                            upload_input.set_input_files(img_path)
                            time.sleep(3)  # 等待上传完成
                        except Exception as e:
                            print(f"[RPA] 图片上传失败: {e}")

            # 填写标题
            print("[RPA] 正在填写标题...")
            try:
                title_input = page.locator(
                    'input[placeholder*="标题"], '
                    '[contenteditable="true"][data-placeholder*="标题"], '
                    ".title-input input"
                ).first
                title_input.click()
                title_input.fill("")
                title_input.type(title[:20], delay=50)
                time.sleep(0.5)
            except Exception as e:
                print(f"[RPA] 填写标题失败: {e}")

            # 填写正文
            print("[RPA] 正在填写正文...")
            try:
                content_input = page.locator(
                    '[contenteditable="true"][data-placeholder*="描述"], '
                    ".desc-input [contenteditable], "
                    'textarea[placeholder*="描述"]'
                ).first
                content_input.click()
                content_input.fill("")
                # 组装正文+标签
                full_content = content
                if tags:
                    tag_str = " ".join(f"#{t}#" for t in tags[:3])
                    full_content = f"{content}\n\n{tag_str}"
                content_input.type(full_content[:1000], delay=20)
                time.sleep(0.5)
            except Exception as e:
                print(f"[RPA] 填写正文失败: {e}")

            # 发布
            print("[RPA] 正在发布...")
            try:
                publish_btn = page.locator(
                    'button:has-text("发布"), '
                    ".publish-btn, "
                    'button:has-text("发表笔记")'
                ).first
                publish_btn.click()
                time.sleep(3)

                result["success"] = True
                result["message"] = "小红书笔记已发布（RPA）"
            except Exception as e:
                result["message"] = f"发布失败: {e}"

            self._save_cookies()

        except Exception as e:
            result["message"] = f"RPA发布异常: {e}"
        finally:
            self.close()

        return result
