#!/usr/bin/env python3
"""多平台内容发布工具 - 命令行工具.

提供命令行接口，支持快速发布内容到多个平台。

使用方法:
    # 基本使用
    python publish.py --title "标题" --content "内容"

    # 从文件读取内容
    python publish.py --title "标题" --content-file article.md

    # 指定平台
    python publish.py --title "标题" --content "内容" --platforms wechat,zhihu

    # 模拟发布
    python publish.py --title "标题" --content "内容" --simulate

    # 真实发布
    python publish.py --title "标题" --content "内容" --real
"""

import argparse
import os
import sys
from typing import List

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.platform_base import PublishMode
from src.core.platform_manager import PlatformManager
from src.platforms.bilibili import BilibiliPlatform
from src.platforms.wechat import WechatPlatform
from src.platforms.xiaohongshu import XiaohongshuPlatform
from src.platforms.zhihu import ZhihuPlatform


def load_content(content: str, content_file: str) -> str:
    """加载内容.

    Args:
        content: 直接提供的内容
        content_file: 内容文件路径

    Returns:
        内容字符串
    """
    if content_file:
        if not os.path.exists(content_file):
            print(f"错误: 文件不存在 - {content_file}")
            sys.exit(1)
        with open(content_file, "r", encoding="utf-8") as f:
            return f.read()
    return content


def load_images(image_paths: List[str]) -> List[str]:
    """加载图片列表.

    Args:
        image_paths: 图片路径列表

    Returns:
        验证后的图片路径列表
    """
    valid_images = []
    for path in image_paths:
        if os.path.exists(path):
            valid_images.append(path)
        else:
            print(f"警告: 图片不存在 - {path}")
    return valid_images


def init_platform_manager(platforms: List[str]) -> PlatformManager:
    """初始化平台管理器.

    Args:
        platforms: 要注册的平台名称列表

    Returns:
        配置好的PlatformManager
    """
    from dotenv import load_dotenv
    load_dotenv()

    manager = PlatformManager()

    available_platforms = {
        "wechat": lambda: WechatPlatform(
            app_id=os.getenv("WECHAT_APP_ID", ""),
            app_secret=os.getenv("WECHAT_APP_SECRET", ""),
        ),
        "zhihu": lambda: ZhihuPlatform(
            username=os.getenv("ZHIHU_USERNAME", ""),
            password=os.getenv("ZHIHU_PASSWORD", ""),
        ),
        "bilibili": lambda: BilibiliPlatform(
            sess_data=os.getenv("BILIBILI_SESS_DATA", ""),
            csrf=os.getenv("BILIBILI_CSRF", ""),
        ),
        "xiaohongshu": lambda: XiaohongshuPlatform(
            cookie=os.getenv("XIAOHONGSHU_COOKIE", ""),
        ),
    }

    for name in platforms:
        if name in available_platforms:
            manager.register(available_platforms[name]())
        else:
            print(f"警告: 未知平台 - {name}")

    return manager


def main() -> None:
    """主函数入口."""
    parser = argparse.ArgumentParser(
        description="多平台内容发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -t "标题" -c "内容"
  %(prog)s -t "标题" -f article.md -p wechat,zhihu
  %(prog)s -t "标题" -c "内容" --simulate
  %(prog)s -t "标题" -c "内容" --real
        """,
    )

    # 内容参数
    parser.add_argument("-t", "--title", required=True, help="文章标题")
    parser.add_argument("-c", "--content", default="", help="文章内容")
    parser.add_argument("-f", "--content-file", help="从文件读取内容")
    parser.add_argument("--tags", default="", help="标签（逗号分隔）")

    # 平台参数
    parser.add_argument(
        "-p", "--platforms",
        default="wechat,zhihu,bilibili,xiaohongshu",
        help="目标平台（逗号分隔，默认全部）",
    )

    # 媒体参数
    parser.add_argument("-i", "--images", nargs="*", default=[], help="图片路径")

    # 发布模式
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--simulate", action="store_true", default=True,
        help="模拟发布（默认）",
    )
    mode_group.add_argument("--real", action="store_true", help="真实发布")

    # 其他参数
    parser.add_argument("--author", default="", help="作者名称")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 加载内容
    content = load_content(args.content, args.content_file)
    if not content:
        print("错误: 内容为空，请使用 -c 或 -f 提供内容")
        sys.exit(1)

    # 加载图片
    images = load_images(args.images)

    # 解析平台
    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]

    # 解析标签
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    # 确定发布模式
    mode = PublishMode.REAL if args.real else PublishMode.SIMULATE

    # 初始化平台管理器
    manager = init_platform_manager(platforms)

    if not manager.platforms:
        print("错误: 没有可用的平台，请检查环境变量配置")
        sys.exit(1)

    # 打印信息
    print("=" * 50)
    print("多平台内容发布工具")
    print("=" * 50)
    print(f"标题: {args.title}")
    print(f"内容: {len(content)} 字符")
    print(f"平台: {', '.join(manager.platforms)}")
    print(f"图片: {len(images)} 张")
    print(f"标签: {', '.join(tags) or '(无)'}")
    print(f"模式: {'真实发布' if mode == PublishMode.REAL else '模拟发布'}")
    print("-" * 50)
    print()

    # 发布
    print("开始发布...\n")

    results = manager.publish_to_all(
        title=args.title,
        content=content,
        images=images,
        mode=mode,
        author=args.author,
        tags=",".join(tags),
    )

    # 显示结果
    print()
    print("=" * 50)
    print(manager.get_summary(results))

    if args.verbose:
        print()
        print("详细结果:")
        for name, result in results.items():
            print(f"\n[{name}]")
            print(f"  成功: {result.success}")
            print(f"  消息: {result.message}")
            if result.url:
                print(f"  链接: {result.url}")

    # 退出码
    success_count = sum(1 for r in results.values() if r.success)
    if success_count == 0 and mode == PublishMode.REAL:
        sys.exit(1)


if __name__ == "__main__":
    main()
