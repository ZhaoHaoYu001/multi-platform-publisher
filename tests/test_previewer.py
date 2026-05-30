"""预览系统测试模块."""

import os
import tempfile

import pytest

from src.review.previewer import Previewer


@pytest.fixture
def temp_dir():
    """创建临时目录."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield tmpdir


@pytest.fixture
def previewer(temp_dir):
    """创建预览生成器实例."""
    output_dir = os.path.join(temp_dir, "previews")
    return Previewer(output_dir=output_dir)


class TestPreviewerInit:
    """预览生成器初始化测试."""

    def test_default_init(self, temp_dir):
        """测试默认初始化."""
        os.chdir(temp_dir)
        previewer = Previewer()
        assert os.path.exists(previewer.output_dir)

    def test_custom_output_dir(self, temp_dir):
        """测试自定义输出目录."""
        output_dir = os.path.join(temp_dir, "custom_previews")
        previewer = Previewer(output_dir=output_dir)
        assert previewer.output_dir == output_dir
        assert os.path.exists(output_dir)


class TestWechatPreview:
    """微信公众号预览测试."""

    def test_generate_basic(self, previewer):
        """测试生成基本预览."""
        path = previewer.generate_wechat_preview(
            title="测试文章",
            content="# 标题\n\n这是内容",
        )
        assert os.path.exists(path)
        assert path.endswith("wechat_preview.html")

        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "测试文章" in html
        assert "微信公众号" in html

    def test_generate_with_author(self, previewer):
        """测试带作者的预览."""
        path = previewer.generate_wechat_preview(
            title="标题",
            content="内容",
            author="张三",
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "张三" in html

    def test_generate_with_images(self, previewer):
        """测试带图片的预览."""
        path = previewer.generate_wechat_preview(
            title="标题",
            content="内容",
            images=["img1.jpg", "img2.jpg"],
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "img1.jpg" in html
        assert "img2.jpg" in html

    def test_markdown_conversion(self, previewer):
        """测试Markdown转换."""
        path = previewer.generate_wechat_preview(
            title="标题",
            content="**粗体**和*斜体*",
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "<strong>粗体</strong>" in html


class TestXiaohongshuPreview:
    """小红书预览测试."""

    def test_generate_basic(self, previewer):
        """测试生成基本预览."""
        path = previewer.generate_xiaohongshu_preview(
            title="分享好物",
            content="这是一篇分享文章",
        )
        assert os.path.exists(path)
        assert path.endswith("xiaohongshu_preview.html")

        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "分享好物" in html
        assert "小红书" in html

    def test_generate_with_images(self, previewer):
        """测试带图片的预览."""
        path = previewer.generate_xiaohongshu_preview(
            title="标题",
            content="内容",
            images=["img1.jpg", "img2.jpg", "img3.jpg"],
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "images-grid" in html
        assert "img1.jpg" in html

    def test_generate_with_tags(self, previewer):
        """测试带标签的预览."""
        path = previewer.generate_xiaohongshu_preview(
            title="标题",
            content="内容",
            tags=["好物分享", "推荐"],
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "#好物分享#" in html
        assert "#推荐#" in html

    def test_max_nine_images(self, previewer):
        """测试最多9张图片."""
        images = [f"img{i}.jpg" for i in range(15)]
        path = previewer.generate_xiaohongshu_preview(
            title="标题",
            content="内容",
            images=images,
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        # 应该只显示前9张
        assert "img8.jpg" in html
        assert "img9.jpg" not in html

    def test_phone_frame_width(self, previewer):
        """测试手机框架宽度."""
        path = previewer.generate_xiaohongshu_preview(
            title="标题",
            content="内容",
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "width: 375px" in html


class TestBilibiliPreview:
    """B站预览测试."""

    def test_generate_basic(self, previewer):
        """测试生成基本预览."""
        path = previewer.generate_bilibili_preview(
            title="B站专栏",
            content="# 标题\n\n这是内容",
        )
        assert os.path.exists(path)
        assert path.endswith("bilibili_preview.html")

        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "B站专栏" in html
        assert "B站专栏" in html

    def test_generate_with_up_name(self, previewer):
        """测试带UP主名称的预览."""
        path = previewer.generate_bilibili_preview(
            title="标题",
            content="内容",
            up_name="科技UP",
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "科技UP" in html

    def test_code_block_style(self, previewer):
        """测试代码块样式."""
        path = previewer.generate_bilibili_preview(
            title="标题",
            content="```python\nprint('hello')\n```",
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "<code>" in html
        assert "print" in html

    def test_container_width(self, previewer):
        """测试容器宽度."""
        path = previewer.generate_bilibili_preview(
            title="标题",
            content="内容",
        )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "max-width: 1000px" in html


class TestGenerateAllPreviews:
    """生成所有预览测试."""

    def test_generate_all(self, previewer):
        """测试生成所有平台预览."""
        results = previewer.generate_all_previews(
            title="测试文章",
            content="# 内容\n\n测试",
            tags=["Python", "教程"],
            author="作者",
        )

        assert "wechat" in results
        assert "xiaohongshu" in results
        assert "bilibili" in results

        for platform, path in results.items():
            assert os.path.exists(path)

    def test_generate_all_with_images(self, previewer):
        """测试带图片生成所有预览."""
        results = previewer.generate_all_previews(
            title="标题",
            content="内容",
            images=["img1.jpg"],
        )

        # 检查微信预览包含图片
        with open(results["wechat"], "r", encoding="utf-8") as f:
            wechat_html = f.read()
        assert "img1.jpg" in wechat_html
