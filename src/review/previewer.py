"""预览系统模块.

本模块提供了为各平台生成HTML预览的功能。
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

import markdown


class Previewer:
    """预览生成器，为各平台生成HTML预览.

    使用示例:
        previewer = Previewer("./previews")

        # 生成微信预览
        html_path = previewer.generate_wechat_preview(
            title="我的文章",
            content="# 标题\n\n内容",
            author="作者名"
        )

        # 生成小红书预览
        html_path = previewer.generate_xiaohongshu_preview(
            title="分享",
            content="内容",
            images=["img1.jpg", "img2.jpg"]
        )

        # 生成B站预览
        html_path = previewer.generate_bilibili_preview(
            title="教程",
            content="内容",
            up_name="UP主"
        )
    """

    def __init__(self, output_dir: str = "./previews") -> None:
        """初始化预览生成器.

        Args:
            output_dir: 预览文件输出目录
        """
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    @property
    def output_dir(self) -> str:
        """获取输出目录路径."""
        return self._output_dir

    def _markdown_to_html(self, content: str) -> str:
        """将Markdown转换为HTML.

        Args:
            content: Markdown内容

        Returns:
            HTML内容
        """
        return markdown.markdown(
            content,
            extensions=["extra", "codehilite", "tables"],
        )

    def _get_current_time(self) -> str:
        """获取当前时间字符串."""
        return datetime.now().strftime("%Y年%m月%d日 %H:%M")

    def generate_wechat_preview(
        self,
        title: str,
        content: str,
        author: str = "",
        images: Optional[List[str]] = None,
    ) -> str:
        """生成微信公众号预览.

        Args:
            title: 文章标题
            content: 文章内容（Markdown格式）
            author: 作者名称
            images: 图片路径列表

        Returns:
            预览HTML文件路径
        """
        content_html = self._markdown_to_html(content)
        time_str = self._get_current_time()
        images = images or []

        # 生成图片HTML
        images_html = ""
        for img in images:
            images_html += f'<img src="{img}" class="wechat-image">\n'

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background-color: #f5f5f5;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        .container {{
            max-width: 677px;
            margin: 20px auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            padding: 30px 20px 20px;
            text-align: center;
        }}
        .title {{
            font-size: 22px;
            font-weight: bold;
            color: #333;
            line-height: 1.4;
            margin-bottom: 15px;
        }}
        .meta {{
            font-size: 14px;
            color: #999;
        }}
        .meta .author {{
            color: #576b95;
        }}
        .content {{
            padding: 20px;
            font-size: 16px;
            line-height: 1.8;
            color: #333;
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .content h1, .content h2, .content h3 {{
            margin: 20px 0 10px;
        }}
        .content img {{
            max-width: 100%;
            height: auto;
            margin: 10px 0;
        }}
        .content blockquote {{
            border-left: 3px solid #d9d9d9;
            padding-left: 15px;
            color: #666;
            margin: 15px 0;
        }}
        .content code {{
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: Consolas, monospace;
        }}
        .content pre {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .images-container {{
            padding: 20px;
        }}
        .wechat-image {{
            max-width: 100%;
            height: auto;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .footer {{
            padding: 20px;
            text-align: center;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">{title}</div>
            <div class="meta">
                <span class="author">{author or '作者'}</span> · {time_str}
            </div>
        </div>
        <div class="content">
            {content_html}
        </div>
        {"<div class='images-container'>" + images_html + "</div>" if images else ""}
        <div class="footer">
            预览模式 · 微信公众号
        </div>
    </div>
</body>
</html>"""

        output_path = os.path.join(self._output_dir, "wechat_preview.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def generate_xiaohongshu_preview(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """生成小红书预览.

        Args:
            title: 笔记标题
            content: 笔记内容（纯文本）
            images: 图片路径列表
            tags: 话题标签列表

        Returns:
            预览HTML文件路径
        """
        images = images or []
        tags = tags or []

        # 生成图片网格
        images_html = ""
        if images:
            images_html = '<div class="images-grid">\n'
            for img in images[:9]:  # 最多9张
                images_html += f'    <div class="image-item"><img src="{img}"></div>\n'
            images_html += '</div>\n'

        # 生成标签
        tags_html = ""
        if tags:
            tags_html = '<div class="tags">\n'
            for tag in tags:
                tags_html += f'    <span class="tag">#{tag}#</span>\n'
            tags_html += '</div>\n'

        # 内容处理（保留换行）
        content_lines = content.replace("\n", "<br>")

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background-color: #f5f5f5;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .phone-frame {{
            width: 375px;
            margin: 20px auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.15);
            overflow: hidden;
        }}
        .status-bar {{
            background: #ff2442;
            color: white;
            padding: 10px 15px;
            font-size: 12px;
            display: flex;
            justify-content: space-between;
        }}
        .note-card {{
            padding: 15px;
        }}
        .images-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2px;
            margin-bottom: 15px;
        }}
        .image-item {{
            aspect-ratio: 1;
            overflow: hidden;
        }}
        .image-item img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .title {{
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            line-height: 1.4;
        }}
        .content {{
            font-size: 14px;
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }}
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .tag {{
            background: #fff0f3;
            color: #ff2442;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 12px;
        }}
        .interaction {{
            display: flex;
            justify-content: space-around;
            padding: 15px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 12px;
        }}
        .interaction span {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
    </style>
</head>
<body>
    <div class="phone-frame">
        <div class="status-bar">
            <span>小红书</span>
            <span>{self._get_current_time()}</span>
        </div>
        <div class="note-card">
            {images_html}
            <div class="title">{title}</div>
            <div class="content">{content_lines}</div>
            {tags_html}
        </div>
        <div class="interaction">
            <span>♡ 0</span>
            <span>💬 0</span>
            <span>⭐ 0</span>
            <span>↗ 分享</span>
        </div>
    </div>
</body>
</html>"""

        output_path = os.path.join(self._output_dir, "xiaohongshu_preview.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def generate_bilibili_preview(
        self,
        title: str,
        content: str,
        up_name: str = "",
        avatar_url: str = "",
        images: Optional[List[str]] = None,
    ) -> str:
        """生成B站专栏预览.

        Args:
            title: 专栏标题
            content: 专栏内容（Markdown格式）
            up_name: UP主名称
            avatar_url: 头像URL
            images: 图片路径列表

        Returns:
            预览HTML文件路径
        """
        content_html = self._markdown_to_html(content)
        images = images or []
        time_str = self._get_current_time()

        # 默认头像
        if not avatar_url:
            avatar_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%2300a1d6'/%3E%3Ctext x='20' y='25' text-anchor='middle' fill='white' font-size='16'%3EUP%3C/text%3E%3C/svg%3E"

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background-color: #f4f5f7;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #00a1d6 0%, #00b5e5 100%);
            padding: 30px 40px;
            color: white;
        }}
        .title {{
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        .author-info {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .avatar {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: 2px solid white;
        }}
        .author-details {{
            flex: 1;
        }}
        .author-name {{
            font-size: 16px;
            font-weight: bold;
        }}
        .publish-time {{
            font-size: 13px;
            opacity: 0.8;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            font-size: 13px;
        }}
        .content {{
            padding: 30px 40px;
            font-size: 16px;
            line-height: 1.8;
            color: #222;
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .content h1, .content h2, .content h3 {{
            margin: 25px 0 15px;
            color: #00a1d6;
        }}
        .content h2 {{
            font-size: 22px;
            border-left: 4px solid #00a1d6;
            padding-left: 10px;
        }}
        .content img {{
            max-width: 100%;
            height: auto;
            margin: 15px 0;
            border-radius: 8px;
        }}
        .content blockquote {{
            background: #f4f5f7;
            border-left: 4px solid #00a1d6;
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }}
        .content code {{
            background: #f4f5f7;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: Consolas, Monaco, monospace;
            font-size: 14px;
            color: #00a1d6;
        }}
        .content pre {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        .content pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        .content ul, .content ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        .content li {{
            margin-bottom: 8px;
        }}
        .footer {{
            padding: 20px 40px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #999;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">{title}</div>
            <div class="author-info">
                <img src="{avatar_url}" class="avatar" alt="avatar">
                <div class="author-details">
                    <div class="author-name">{up_name or 'UP主'}</div>
                    <div class="publish-time">{time_str}</div>
                </div>
                <div class="stats">
                    <span>阅读 0</span>
                    <span>评论 0</span>
                    <span>收藏 0</span>
                </div>
            </div>
        </div>
        <div class="content">
            {content_html}
        </div>
        <div class="footer">
            预览模式 · B站专栏
        </div>
    </div>
</body>
</html>"""

        output_path = os.path.join(self._output_dir, "bilibili_preview.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def generate_all_previews(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
        author: str = "",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """为所有平台生成预览.

        Args:
            title: 标题
            content: 内容
            images: 图片列表
            author: 作者/UP主名称
            tags: 标签列表

        Returns:
            平台名称到预览文件路径的映射
        """
        results = {}

        results["wechat"] = self.generate_wechat_preview(
            title=title,
            content=content,
            author=author,
            images=images,
        )

        results["xiaohongshu"] = self.generate_xiaohongshu_preview(
            title=title,
            content=content,
            images=images,
            tags=tags,
        )

        results["bilibili"] = self.generate_bilibili_preview(
            title=title,
            content=content,
            up_name=author,
            images=images,
        )

        return results
