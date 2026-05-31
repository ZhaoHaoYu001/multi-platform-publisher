"""B站RPA浏览器自动化模块."""

import os
import time
from typing import Any, Dict, List, Optional

from .base_rpa import BaseRPA


class BilibiliRPA(BaseRPA):
    """B站专栏RPA自动化发布.

    流程:
    1. 登录（手动/Cookie自动）
    2. 打开专栏编辑器
    3. 填写标题和正文
    4. 可选上传图片/添加标签
    5. 发布或存草稿
    """

    PLATFORM = "bilibili"
    LOGIN_URL = "https://passport.bilibili.com/login"
    HOME_URL = "www.bilibili.com"

    def _check_login_indicator(self, page) -> bool:
        """检查B站登录状态."""
        try:
            # 检查是否存在用户头像（登录标志）
            page.wait_for_selector(".header-avatar-wrap", timeout=3000)
            return True
        except Exception:
            return False

    def publish(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        save_as_draft: bool = True,
    ) -> Dict[str, Any]:
        """发布B站专栏文章.

        Args:
            title: 文章标题
            content: 文章内容（HTML格式）
            images: 图片路径列表
            tags: 标签列表
            save_as_draft: 是否仅保存为草稿

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

            # 打开专栏编辑器
            print("[RPA] 正在打开B站专栏编辑器...")
            page.goto(
                "https://member.bilibili.com/article-text/home",
                wait_until="domcontentloaded",
            )
            time.sleep(3)

            # 检查是否成功进入编辑器
            if "passport.bilibili.com" in page.url:
                # Cookie过期，重新登录
                self._context.close()
                self._create_context()
                page = self._new_page()
                if not self.login():
                    result["message"] = "重新登录失败"
                    return result
                page.goto(
                    "https://member.bilibili.com/article-text/home",
                    wait_until="domcontentloaded",
                )
                time.sleep(3)

            # 填写标题
            print("[RPA] 正在填写标题...")
            title_input = page.locator("#article-title input, .title-input input").first
            title_input.click()
            title_input.fill("")
            title_input.type(title, delay=50)
            time.sleep(1)

            # 填写正文（通过contenteditable div）
            print("[RPA] 正在填写正文...")
            editor = page.locator("#article-content .ql-editor, .editor-content .ql-editor").first
            editor.click()
            # 使用JavaScript注入HTML内容
            page.evaluate(
                """(html) => {
                    const editor = document.querySelector('#article-content .ql-editor') ||
                                   document.querySelector('.editor-content .ql-editor');
                    if (editor) editor.innerHTML = html;
                }""",
                content,
            )
            time.sleep(1)

            # 上传图片
            if images:
                print(f"[RPA] 正在上传 {len(images)} 张图片...")
                for img_path in images:
                    if os.path.exists(img_path):
                        try:
                            # 查找上传按钮
                            upload_input = page.locator(
                                'input[type="file"][accept*="image"]'
                            ).first
                            upload_input.set_input_files(img_path)
                            time.sleep(2)  # 等待上传完成
                        except Exception as e:
                            print(f"[RPA] 图片上传失败: {e}")

            # 添加标签
            if tags:
                print("[RPA] 正在添加标签...")
                for tag in tags[:5]:  # B站最多5个标签
                    try:
                        tag_input = page.locator(
                            '.tag-input input, input[placeholder*="标签"]'
                        ).first
                        tag_input.click()
                        tag_input.fill(tag)
                        tag_input.press("Enter")
                        time.sleep(0.5)
                    except Exception:
                        pass

            # 发布或存草稿
            if save_as_draft:
                print("[RPA] 正在保存草稿...")
                try:
                    draft_btn = page.locator(
                        'button:has-text("存草稿"), .save-draft-btn'
                    ).first
                    draft_btn.click()
                    time.sleep(2)
                    result["success"] = True
                    result["message"] = "B站专栏已保存为草稿（RPA）"
                except Exception as e:
                    result["message"] = f"保存草稿失败: {e}"
            else:
                print("[RPA] 正在发布...")
                try:
                    publish_btn = page.locator(
                        'button:has-text("发布"), .submit-btn'
                    ).first
                    publish_btn.click()
                    time.sleep(3)

                    # 检查是否弹出确认框
                    try:
                        confirm_btn = page.locator(
                            'button:has-text("确认"), .confirm-btn'
                        ).first
                        confirm_btn.click(timeout=5000)
                        time.sleep(2)
                    except Exception:
                        pass

                    result["success"] = True
                    result["message"] = "B站专栏已发布（RPA）"
                except Exception as e:
                    result["message"] = f"发布失败: {e}"

            # 保存最新Cookie
            self._save_cookies()

        except Exception as e:
            result["message"] = f"RPA发布异常: {e}"
        finally:
            self.close()

        return result
