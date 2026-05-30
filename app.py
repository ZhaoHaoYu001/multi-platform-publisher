#!/usr/bin/env python3
"""多平台内容发布工具 - 交互式主程序.

提供菜单驱动的交互式界面，支持内容编辑、媒体管理、预览和发布。

使用方法:
    python app.py
"""

import os
import sys
from typing import List, Optional

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.platform_base import PublishMode
from src.core.platform_manager import PlatformManager
from src.draft.draft_manager import DraftManager
from src.media.media_manager import MediaManager
from src.platforms.bilibili import BilibiliPlatform
from src.platforms.wechat import WechatPlatform
from src.platforms.xiaohongshu import XiaohongshuPlatform
from src.platforms.zhihu import ZhihuPlatform
from src.review.previewer import Previewer


class App:
    """交互式应用程序.

    提供完整的草稿编辑、媒体管理、预览和发布功能。
    """

    def __init__(self) -> None:
        """初始化应用程序."""
        self.draft_manager = DraftManager()
        self.media_manager = MediaManager()
        self.previewer = Previewer()
        self.platform_manager = PlatformManager()

        # 注册平台（使用环境变量配置）
        self._init_platforms()

        # 当前草稿
        self.current_title = ""
        self.current_content = ""
        self.current_tags: List[str] = []
        self.current_category = ""

    def _init_platforms(self) -> None:
        """初始化平台."""
        from dotenv import load_dotenv
        load_dotenv()

        # 微信公众号
        wechat_app_id = os.getenv("WECHAT_APP_ID")
        wechat_app_secret = os.getenv("WECHAT_APP_SECRET")
        if wechat_app_id and wechat_app_secret:
            self.platform_manager.register(
                WechatPlatform(app_id=wechat_app_id, app_secret=wechat_app_secret)
            )

        # 知乎
        self.platform_manager.register(ZhihuPlatform())

        # B站
        bilibili_sess = os.getenv("BILIBILI_SESS_DATA")
        bilibili_csrf = os.getenv("BILIBILI_CSRF")
        if bilibili_sess:
            self.platform_manager.register(
                BilibiliPlatform(sess_data=bilibili_sess, csrf=bilibili_csrf)
            )

        # 小红书
        self.platform_manager.register(XiaohongshuPlatform())

    def clear_screen(self) -> None:
        """清屏."""
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self) -> None:
        """打印头部信息."""
        print("=" * 50)
        print("       多平台内容发布工具")
        print("=" * 50)
        print(f"当前标题: {self.current_title or '(未设置)'}")
        print(f"内容长度: {len(self.current_content)} 字符")
        print(f"标签: {', '.join(self.current_tags) or '(无)'}")
        print(f"媒体: {self.media_manager.count} 项")
        print(f"平台: {', '.join(self.platform_manager.platforms) or '(无)'}")
        print("-" * 50)

    def print_menu(self) -> None:
        """打印主菜单."""
        print("\n请选择操作:")
        print("  1. 编辑内容（标题/正文/标签）")
        print("  2. 管理媒体（添加/删除/说明/排序）")
        print("  3. 预览效果")
        print("  4. 选择平台并发布")
        print("  5. 草稿管理")
        print("  6. 帮助")
        print("  0. 保存并退出")
        print()

    def edit_content(self) -> None:
        """编辑内容."""
        while True:
            self.clear_screen()
            print("=== 编辑内容 ===")
            print(f"1. 标题: {self.current_title or '(未设置)'}")
            print(f"2. 正文: {len(self.current_content)} 字符")
            print(f"3. 标签: {', '.join(self.current_tags) or '(无)'}")
            print(f"4. 分类: {self.current_category or '(未设置)'}")
            print("0. 返回主菜单")
            print()

            choice = input("请选择: ").strip()

            if choice == "1":
                title = input(f"输入标题 (当前: {self.current_title}): ").strip()
                if title:
                    self.current_title = title
                    print("✓ 标题已更新")
            elif choice == "2":
                print("输入正文内容 (输入END结束):")
                lines = []
                while True:
                    line = input()
                    if line == "END":
                        break
                    lines.append(line)
                if lines:
                    self.current_content = "\n".join(lines)
                    print(f"✓ 内容已更新 ({len(self.current_content)} 字符)")
            elif choice == "3":
                tags = input("输入标签 (逗号分隔): ").strip()
                if tags:
                    self.current_tags = [t.strip() for t in tags.split(",") if t.strip()]
                    print(f"✓ 标签已更新: {self.current_tags}")
            elif choice == "4":
                category = input(f"输入分类 (当前: {self.current_category}): ").strip()
                if category:
                    self.current_category = category
                    print("✓ 分类已更新")
            elif choice == "0":
                break

            input("\n按回车继续...")

    def manage_media(self) -> None:
        """管理媒体."""
        while True:
            self.clear_screen()
            print("=== 管理媒体 ===")
            print(f"当前媒体: {self.media_manager.count} 项")
            print()

            if self.media_manager.items:
                for i, item in enumerate(self.media_manager.items, 1):
                    type_str = "图片" if item.media_type.value == "image" else "视频"
                    print(f"  {i}. [{type_str}] {item.filename} - {item.caption or '(无说明)'}")
                print()

            print("操作:")
            print("  1. 添加图片")
            print("  2. 添加视频")
            print("  3. 删除媒体")
            print("  4. 更新说明")
            print("  5. 调整排序")
            print("  0. 返回主菜单")
            print()

            choice = input("请选择: ").strip()

            if choice == "1":
                path = input("输入图片路径: ").strip()
                if path and os.path.exists(path):
                    caption = input("输入说明 (可选): ").strip()
                    try:
                        self.media_manager.add_image(path, caption=caption)
                        print("✓ 图片已添加")
                    except Exception as e:
                        print(f"✗ 添加失败: {e}")
                else:
                    print("✗ 文件不存在")
            elif choice == "2":
                path = input("输入视频路径: ").strip()
                if path and os.path.exists(path):
                    caption = input("输入说明 (可选): ").strip()
                    try:
                        self.media_manager.add_video(path, caption=caption)
                        print("✓ 视频已添加")
                    except Exception as e:
                        print(f"✗ 添加失败: {e}")
                else:
                    print("✗ 文件不存在")
            elif choice == "3":
                idx = input("输入要删除的序号: ").strip()
                try:
                    item = self.media_manager.items[int(idx) - 1]
                    self.media_manager.remove_item(item.path)
                    print("✓ 已删除")
                except (IndexError, ValueError):
                    print("✗ 无效序号")
            elif choice == "4":
                idx = input("输入要更新说明的序号: ").strip()
                try:
                    item = self.media_manager.items[int(idx) - 1]
                    caption = input("输入新说明: ").strip()
                    self.media_manager.update_caption(item.path, caption)
                    print("✓ 说明已更新")
                except (IndexError, ValueError):
                    print("✗ 无效序号")
            elif choice == "0":
                break

            input("\n按回车继续...")

    def preview(self) -> None:
        """预览效果."""
        if not self.current_title and not self.current_content:
            print("✗ 请先编辑内容")
            input("按回车继续...")
            return

        self.clear_screen()
        print("=== 生成预览 ===")

        images = [item.path for item in self.media_manager.images]

        try:
            results = self.previewer.generate_all_previews(
                title=self.current_title,
                content=self.current_content,
                images=images,
                tags=self.current_tags,
            )

            print("\n预览文件已生成:")
            for platform, path in results.items():
                print(f"  {platform}: {path}")

            print("\n请在浏览器中打开上述文件查看效果。")

        except Exception as e:
            print(f"✗ 预览生成失败: {e}")

        input("\n按回车继续...")

    def publish(self) -> None:
        """发布内容."""
        if not self.current_title:
            print("✗ 请先设置标题")
            input("按回车继续...")
            return

        if not self.platform_manager.platforms:
            print("✗ 未配置任何平台")
            input("按回车继续...")
            return

        self.clear_screen()
        print("=== 选择平台并发布 ===")
        print()

        platforms = self.platform_manager.platforms
        for i, name in enumerate(platforms, 1):
            print(f"  {i}. {name}")
        print(f"  {len(platforms) + 1}. 全部平台")
        print("  0. 取消")
        print()

        choice = input("选择平台 (序号): ").strip()

        if choice == "0":
            return

        # 选择发布模式
        mode_choice = input("发布模式 (1=模拟, 2=真实, 默认=模拟): ").strip()
        mode = PublishMode.REAL if mode_choice == "2" else PublishMode.SIMULATE

        images = [item.path for item in self.media_manager.images]

        print(f"\n发布模式: {'真实' if mode == PublishMode.REAL else '模拟'}")
        print("开始发布...\n")

        if choice == str(len(platforms) + 1):
            # 发布到所有平台
            results = self.platform_manager.publish_to_all(
                title=self.current_title,
                content=self.current_content,
                images=images,
                mode=mode,
                tags=",".join(self.current_tags),
            )
        else:
            # 发布到指定平台
            try:
                platform_name = platforms[int(choice) - 1]
                result = self.platform_manager.publish_to_platform(
                    platform_name=platform_name,
                    title=self.current_title,
                    content=self.current_content,
                    images=images,
                    mode=mode,
                    tags=",".join(self.current_tags),
                )
                results = {platform_name: result}
            except (IndexError, ValueError):
                print("✗ 无效选择")
                input("按回车继续...")
                return

        # 显示结果
        print("\n" + self.platform_manager.get_summary(results))

        input("\n按回车继续...")

    def draft_management(self) -> None:
        """草稿管理."""
        while True:
            self.clear_screen()
            print("=== 草稿管理 ===")
            print()

            drafts = self.draft_manager.list_drafts()
            if drafts:
                print("已有草稿:")
                for i, d in enumerate(drafts[:10], 1):
                    print(f"  {i}. {d.get('title', '无标题')} (版本 {d.get('version', 1)})")
                print()

            print("操作:")
            print("  1. 保存当前为草稿")
            print("  2. 加载草稿")
            print("  3. 导出为Markdown")
            print("  4. 删除草稿")
            print("  0. 返回主菜单")
            print()

            choice = input("请选择: ").strip()

            if choice == "1":
                draft = self.draft_manager.new_draft(
                    title=self.current_title,
                    content=self.current_content,
                    tags=self.current_tags,
                    category=self.current_category,
                )
                draft_id = self.draft_manager.save_current(draft)
                print(f"✓ 草稿已保存 (ID: {draft_id})")

            elif choice == "2":
                idx = input("输入要加载的序号: ").strip()
                try:
                    draft_info = drafts[int(idx) - 1]
                    draft = self.draft_manager.load_draft(draft_info["id"])
                    self.current_title = draft.content.title
                    self.current_content = draft.content.content
                    self.current_tags = draft.content.tags
                    self.current_category = draft.content.category
                    print("✓ 草稿已加载")
                except (IndexError, ValueError):
                    print("✗ 无效序号")

            elif choice == "3":
                idx = input("输入要导出的序号: ").strip()
                try:
                    draft_info = drafts[int(idx) - 1]
                    output = input("输出文件路径 (默认: export.md): ").strip() or "export.md"
                    self.draft_manager.export(draft_info["id"], output)
                    print(f"✓ 已导出到 {output}")
                except (IndexError, ValueError):
                    print("✗ 无效序号")

            elif choice == "4":
                idx = input("输入要删除的序号: ").strip()
                try:
                    draft_info = drafts[int(idx) - 1]
                    self.draft_manager.delete_draft(draft_info["id"])
                    print("✓ 已删除")
                except (IndexError, ValueError):
                    print("✗ 无效序号")

            elif choice == "0":
                break

            input("\n按回车继续...")

    def show_help(self) -> None:
        """显示帮助信息."""
        self.clear_screen()
        print("=== 帮助 ===")
        print()
        print("多平台内容发布工具 - 使用说明")
        print()
        print("1. 编辑内容: 设置标题、正文、标签和分类")
        print("2. 管理媒体: 添加/删除图片和视频，设置说明和排序")
        print("3. 预览效果: 生成微信/小红书/B站的HTML预览")
        print("4. 选择平台并发布: 模拟或真实发布到各平台")
        print("5. 草稿管理: 保存/加载/导出/删除草稿")
        print()
        print("环境变量配置 (.env文件):")
        print("  WECHAT_APP_ID       - 微信公众号AppID")
        print("  WECHAT_APP_SECRET   - 微信公众号AppSecret")
        print("  BILIBILI_SESS_DATA  - B站SESSDATA")
        print("  BILIBILI_CSRF       - B站CSRF Token")
        print()
        input("按回车返回...")

    def run(self) -> None:
        """运行应用程序."""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_menu()

            choice = input("请选择 (0-6): ").strip()

            if choice == "1":
                self.edit_content()
            elif choice == "2":
                self.manage_media()
            elif choice == "3":
                self.preview()
            elif choice == "4":
                self.publish()
            elif choice == "5":
                self.draft_management()
            elif choice == "6":
                self.show_help()
            elif choice == "0":
                # 自动保存草稿
                if self.current_title or self.current_content:
                    draft = self.draft_manager.new_draft(
                        title=self.current_title,
                        content=self.current_content,
                        tags=self.current_tags,
                        category=self.current_category,
                    )
                    self.draft_manager.save_current(draft)
                    print("✓ 草稿已自动保存")
                print("再见!")
                break
            else:
                print("无效选择")
                input("按回车继续...")


def main() -> None:
    """主函数入口."""
    # 设置UTF-8编码（Windows兼容）
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    app = App()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\n程序被中断，再见!")
    except Exception as e:
        print(f"\n程序出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
