"""知乎RPA浏览器自动化模块."""

import os
import time
from typing import Any, Dict, List, Optional

from .base_rpa import BaseRPA


class ZhihuRPA(BaseRPA):
    """知乎专栏RPA自动化发布.

    流程:
    1. 登录（手动/Cookie自动）
    2. 打开知乎文章编辑器
    3. 填写标题和正文（支持Markdown）
    4. 发布
    """

    PLATFORM = "zhihu"
    LOGIN_URL = "https://www.zhihu.com/signin"
    HOME_URL = "www.zhihu.com"

    def _check_login_indicator(self, page) -> bool:
        """检查知乎登录状态."""
        try:
            page.wait_for_selector(
                ".AppHeader-avatar, .Avatar, [class*='avatar']",
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
    ) -> Dict[str, Any]:
        """发布知乎文章.

        Args:
            title: 文章标题
            content: 文章内容（Markdown格式）
            images: 图片路径列表

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

            # 打开知乎文章编辑器
            print("[RPA] 正在打开知乎文章编辑器...")
            page.goto(
                "https://zhuanlan.zhihu.com/p/write",
                wait_until="domcontentloaded",
            )
            time.sleep(3)

            # 检查登录状态
            if "signin" in page.url.lower():
                self._context.close()
                self._create_context()
                page = self._new_page()
                if not self.login():
                    result["message"] = "重新登录失败"
                    return result
                page.goto(
                    "https://zhuanlan.zhihu.com/p/write",
                    wait_until="domcontentloaded",
                )
                time.sleep(3)

            # 填写标题
            print("[RPA] 正在填写标题...")
            try:
                title_input = page.locator(
                    '.WriteIndex-titleInput textarea, '
                    'textarea[placeholder*="标题"], '
                    ".WriteTitle textarea"
                ).first
                title_input.click()
                title_input.fill("")
                title_input.type(title[:100], delay=50)
                time.sleep(0.5)
            except Exception as e:
                print(f"[RPA] 填写标题失败: {e}")

            # 填写正文
            print("[RPA] 正在填写正文...")
            try:
                editor = page.locator(
                    '.RichText-iframe, '
                    '.public-DraftEditor-content, '
                    '[contenteditable="true"]'
                ).first
                editor.click()
                time.sleep(0.5)

                # 通过JavaScript注入内容
                page.evaluate(
                    """(text) => {
                        const editor = document.querySelector('.public-DraftEditor-content') ||
                                       document.querySelector('[contenteditable="true"]');
                        if (editor) {
                            editor.focus();
                            document.execCommand('insertText', false, text);
                        }
                    }""",
                    content[:20000],
                )
                time.sleep(1)
            except Exception as e:
                print(f"[RPA] 填写正文失败: {e}")

            # 插入图片
            if images:
                print(f"[RPA] 正在插入 {len(images)} 张图片...")
                for img_path in images[:30]:
                    if os.path.exists(img_path):
                        try:
                            # 点击图片插入按钮
                            img_btn = page.locator(
                                'button[aria-label*="图片"], '
                                '.WriterTool-icon img, '
                                'svg[aria-label="插入图片"]'
                            ).first
                            img_btn.click()
                            time.sleep(1)

                            # 上传文件
                            upload_input = page.locator(
                                'input[type="file"][accept*="image"]'
                            ).first
                            upload_input.set_input_files(img_path)
                            time.sleep(3)
                        except Exception as e:
                            print(f"[RPA] 图片插入失败: {e}")

            # 发布
            print("[RPA] 正在发布...")
            try:
                publish_btn = page.locator(
                    'button:has-text("发布"), '
                    ".PublishButton, "
                    'button:has-text("发表文章")'
                ).first
                publish_btn.click()
                time.sleep(2)

                # 可能有确认弹窗
                try:
                    confirm = page.locator(
                        'button:has-text("确认发布"), '
                        'button:has-text("确定")'
                    ).first
                    confirm.click(timeout=5000)
                    time.sleep(2)
                except Exception:
                    pass

                result["success"] = True
                result["message"] = "知乎文章已发布（RPA）"
            except Exception as e:
                result["message"] = f"发布失败: {e}"

            self._save_cookies()

        except Exception as e:
            result["message"] = f"RPA发布异常: {e}"
        finally:
            self.close()

        return result
