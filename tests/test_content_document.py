"""ContentDocument 和 ContentParser 测试."""

import pytest

from src.core.content_document import ContentDocument, ContentSection, ImageRef
from src.core.content_parser import ContentParser


class TestContentDocument:
    """ContentDocument 数据类测试."""

    def test_create_empty(self):
        doc = ContentDocument()
        assert doc.title == ""
        assert doc.body == []
        assert doc.images == []
        assert doc.tags == []

    def test_create_with_data(self):
        doc = ContentDocument(
            title="测试标题",
            body=[ContentSection(section_type="paragraph", text="正文")],
            tags=["Python", "教程"],
        )
        assert doc.title == "测试标题"
        assert len(doc.body) == 1
        assert len(doc.tags) == 2

    def test_to_markdown(self):
        doc = ContentDocument(
            title="文章标题",
            body=[
                ContentSection(section_type="heading", level=2, text="小标题"),
                ContentSection(section_type="paragraph", text="这是正文段落。"),
            ],
            tags=["测试"],
            category="技术",
        )
        md = doc.to_markdown()
        assert "# 文章标题" in md
        assert "## 小标题" in md
        assert "这是正文段落。" in md

    def test_to_plain_text(self):
        doc = ContentDocument(
            title="标题",
            body=[
                ContentSection(section_type="paragraph", text="这是**加粗**和*斜体*文字。"),
            ],
        )
        plain = doc.to_plain_text()
        assert "**加粗**" not in plain
        assert "加粗" in plain

    def test_get_word_count_chinese(self):
        doc = ContentDocument(
            body=[ContentSection(section_type="paragraph", text="这是一个测试段落")]
        )
        count = doc.get_word_count()
        assert count == 8  # 8个中文字符

    def test_get_image_count(self):
        doc = ContentDocument(
            images=[ImageRef(src="a.jpg"), ImageRef(src="b.jpg")]
        )
        assert doc.get_image_count() == 2


class TestContentSection:
    """ContentSection 测试."""

    def test_plain_text_paragraph(self):
        section = ContentSection(section_type="paragraph", text="普通段落")
        assert section.get_plain_text() == "普通段落"

    def test_plain_text_code(self):
        section = ContentSection(
            section_type="code",
            text="print(hello)",
            metadata={"language": "python"},
        )
        plain = section.get_plain_text()
        assert "python" in plain
        assert "print(hello)" in plain

    def test_plain_text_blockquote(self):
        section = ContentSection(section_type="blockquote", text="引用内容\n第二行")
        plain = section.get_plain_text()
        assert "> 引用内容" in plain
        assert "> 第二行" in plain

    def test_plain_text_unordered_list(self):
        section = ContentSection(
            section_type="list",
            children=[
                ContentSection(section_type="paragraph", text="项目1"),
                ContentSection(section_type="paragraph", text="项目2"),
            ],
            metadata={"list_type": "unordered"},
        )
        plain = section.get_plain_text()
        assert "- 项目1" in plain
        assert "- 项目2" in plain

    def test_plain_text_ordered_list(self):
        section = ContentSection(
            section_type="list",
            children=[
                ContentSection(section_type="paragraph", text="第一项"),
                ContentSection(section_type="paragraph", text="第二项"),
            ],
            metadata={"list_type": "ordered"},
        )
        plain = section.get_plain_text()
        assert "1. 第一项" in plain
        assert "2. 第二项" in plain

    def test_plain_text_divider(self):
        section = ContentSection(section_type="divider")
        assert section.get_plain_text() == "---"


class TestContentParser:
    """ContentParser 测试."""

    def setup_method(self):
        self.parser = ContentParser()

    def test_parse_empty(self):
        doc = self.parser.parse("")
        assert doc.title == ""
        assert doc.body == []

    def test_parse_title_from_h1(self):
        doc = self.parser.parse("# 文章标题\n\n正文内容")
        assert doc.title == "文章标题"
        assert len(doc.body) == 1

    def test_parse_explicit_title(self):
        doc = self.parser.parse("# 被忽略的标题\n\n正文", title="显式标题")
        assert doc.title == "显式标题"

    def test_parse_headings(self):
        md = "## H2\n\n### H3\n\n正文"
        doc = self.parser.parse(md, title="H1")
        headings = [s for s in doc.body if s.section_type == "heading"]
        assert len(headings) == 2

    def test_parse_paragraphs(self):
        md = "第一段。\n\n第二段。\n\n第三段。"
        doc = self.parser.parse(md)
        paras = [s for s in doc.body if s.section_type == "paragraph"]
        assert len(paras) == 3

    def test_parse_code_block(self):
        md = "正文\n\n```python\nprint(hello)\n```\n\n后续"
        doc = self.parser.parse(md)
        codes = [s for s in doc.body if s.section_type == "code"]
        assert len(codes) == 1
        assert codes[0].metadata["language"] == "python"

    def test_parse_code_block_no_lang(self):
        md = "```\ncode here\n```"
        doc = self.parser.parse(md)
        codes = [s for s in doc.body if s.section_type == "code"]
        assert len(codes) == 1
        assert codes[0].metadata["language"] == ""

    def test_parse_blockquote(self):
        md = "正文\n\n> 引用内容\n> 第二行"
        doc = self.parser.parse(md)
        quotes = [s for s in doc.body if s.section_type == "blockquote"]
        assert len(quotes) == 1
        assert "引用" in quotes[0].text

    def test_parse_unordered_list(self):
        md = "正文\n\n- 项目1\n- 项目2\n- 项目3"
        doc = self.parser.parse(md)
        lists = [s for s in doc.body if s.section_type == "list"]
        assert len(lists) == 1
        assert len(lists[0].children) == 3
        assert lists[0].metadata["list_type"] == "unordered"

    def test_parse_ordered_list(self):
        md = "正文\n\n1. 第一项\n2. 第二项\n3. 第三项"
        doc = self.parser.parse(md)
        lists = [s for s in doc.body if s.section_type == "list"]
        assert len(lists) == 1
        assert len(lists[0].children) == 3
        assert lists[0].metadata["list_type"] == "ordered"

    def test_parse_divider(self):
        md = "上文\n\n---\n\n下文"
        doc = self.parser.parse(md)
        dividers = [s for s in doc.body if s.section_type == "divider"]
        assert len(dividers) == 1

    def test_parse_inline_image(self):
        md = '正文\n\n![风景](photo.jpg "风景照片")'
        doc = self.parser.parse(md)
        assert len(doc.images) == 1
        assert doc.images[0].src == "photo.jpg"
        assert doc.images[0].alt == "风景"
        assert doc.images[0].title == "风景照片"

    def test_parse_multiple_images(self):
        md = "![img1](a.jpg)\n\n文字\n\n![img2](b.png)"
        doc = self.parser.parse(md)
        assert len(doc.images) == 2

    def test_parse_tags(self):
        doc = self.parser.parse("正文", tags=["Python", "教程"])
        assert doc.tags == ["Python", "教程"]

    def test_parse_complex_document(self):
        md = """# Python异步编程入门

## 什么是异步编程

异步编程是一种并发编程方式。

## 基本用法

```python
import asyncio

async def main():
    print('hello')

asyncio.run(main())
```

## 总结

- 异步提高了IO效率
- asyncio是Python的标准库

---

感谢阅读！
"""
        doc = self.parser.parse(md, tags=["Python", "异步"])
        assert doc.title == "Python异步编程入门"

        headings = [s for s in doc.body if s.section_type == "heading"]
        codes = [s for s in doc.body if s.section_type == "code"]
        lists = [s for s in doc.body if s.section_type == "list"]
        dividers = [s for s in doc.body if s.section_type == "divider"]

        assert len(headings) == 3  # 3个H2
        assert len(codes) == 1
        assert codes[0].metadata["language"] == "python"
        assert len(lists) == 1
        assert len(lists[0].children) == 2
        assert len(dividers) == 1


class TestFromDraft:
    """从 Draft 创建 ContentDocument 测试."""

    def test_from_draft(self):
        from src.draft.draft_manager import Draft, ContentDraft

        draft = Draft(
            content=ContentDraft(
                title="草稿标题",
                content="# 正文\n\n内容",
                tags=["tag1"],
                category="cat",
            )
        )
        doc = ContentDocument.from_draft(draft)
        assert doc.title == "草稿标题"
        assert doc.tags == ["tag1"]
