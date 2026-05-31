"""Markdown 内容解析器.

将 Markdown 文本解析为 ContentDocument 结构化模型。
支持标题、段落、代码块、引用、列表、图片、分隔线等块级元素。
"""

import re
from typing import List, Optional

from .content_document import ContentDocument, ContentSection, ImageRef


class ContentParser:
    """Markdown → ContentDocument 解析器.

    使用示例:
        parser = ContentParser()
        doc = parser.parse("# 标题\n\n正文内容", tags=["Python"])
        print(doc.title)  # "标题"
    """

    # 正则模式
    _HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
    _CODE_FENCE_RE = re.compile(r"^```(\w*)")
    _BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)")
    _UNORDERED_LIST_RE = re.compile(r"^(\s*)[-*+]\s+(.+)")
    _ORDERED_LIST_RE = re.compile(r"^(\s*)\d+\.\s+(.+)")
    _IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
    _DIVIDER_RE = re.compile(r"^[-*_]{3,}\s*$")

    def parse(
        self,
        markdown_text: str,
        title: str = "",
        tags: Optional[List[str]] = None,
    ) -> ContentDocument:
        """解析 Markdown 文本为 ContentDocument.

        Args:
            markdown_text: Markdown 格式的文本
            title: 文章标题（为空则从首个 H1 提取）
            tags: 标签列表

        Returns:
            ContentDocument 实例
        """
        if not markdown_text:
            return ContentDocument(title=title or "", tags=tags or [])

        lines = markdown_text.split("\n")

        # 提取标题
        actual_title = title
        start_idx = 0
        if not actual_title and lines:
            m = self._HEADING_RE.match(lines[0])
            if m and len(m.group(1)) == 1:  # H1
                actual_title = m.group(2).strip()
                start_idx = 1
                # 跳过标题后的空行
                if start_idx < len(lines) and lines[start_idx].strip() == "":
                    start_idx += 1

        # 提取元数据行（> 分类: xxx | 标签: xxx）
        actual_tags = tags or []
        category = ""
        if start_idx < len(lines):
            meta_match = re.match(r"^>\s*(?:分类:\s*(.+?))?\s*(?:\|\s*标签:\s*(.+?))?\s*$", lines[start_idx])
            if meta_match:
                if meta_match.group(1):
                    category = meta_match.group(1).strip()
                if meta_match.group(2) and not actual_tags:
                    actual_tags = [t.strip() for t in meta_match.group(2).split(",")]
                start_idx += 1
                if start_idx < len(lines) and lines[start_idx].strip() == "":
                    start_idx += 1

        # 提取正文段落
        body_lines = lines[start_idx:]
        body = self._parse_blocks(body_lines)

        # 提取所有图片引用
        images = self._extract_images(markdown_text)

        return ContentDocument(
            title=actual_title or "",
            body=body,
            images=images,
            tags=actual_tags,
            category=category,
        )

    def _parse_blocks(self, lines: List[str]) -> List[ContentSection]:
        """将行列表解析为块级段落列表."""
        sections: List[ContentSection] = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 空行跳过
            if not line.strip():
                i += 1
                continue

            # 分隔线
            if self._DIVIDER_RE.match(line.strip()):
                sections.append(ContentSection(section_type="divider"))
                i += 1
                continue

            # 代码块
            fence_match = self._CODE_FENCE_RE.match(line.strip())
            if fence_match:
                lang = fence_match.group(1) or ""
                code_lines: List[str] = []
                i += 1
                while i < len(lines):
                    if lines[i].strip().startswith("```"):
                        i += 1
                        break
                    code_lines.append(lines[i])
                    i += 1
                sections.append(ContentSection(
                    section_type="code",
                    text="\n".join(code_lines),
                    metadata={"language": lang},
                ))
                continue

            # 标题
            heading_match = self._HEADING_RE.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                sections.append(ContentSection(
                    section_type="heading",
                    level=level,
                    text=text,
                ))
                i += 1
                continue

            # 引用块
            if self._BLOCKQUOTE_RE.match(line):
                quote_lines: List[str] = []
                while i < len(lines) and self._BLOCKQUOTE_RE.match(lines[i]):
                    m = self._BLOCKQUOTE_RE.match(lines[i])
                    if m:
                        quote_lines.append(m.group(1))
                    i += 1
                sections.append(ContentSection(
                    section_type="blockquote",
                    text="\n".join(quote_lines),
                ))
                continue

            # 无序列表
            if self._UNORDERED_LIST_RE.match(line):
                items: List[ContentSection] = []
                while i < len(lines) and self._UNORDERED_LIST_RE.match(lines[i]):
                    m = self._UNORDERED_LIST_RE.match(lines[i])
                    if m:
                        items.append(ContentSection(
                            section_type="paragraph",
                            text=m.group(2),
                        ))
                    i += 1
                sections.append(ContentSection(
                    section_type="list",
                    children=items,
                    metadata={"list_type": "unordered"},
                ))
                continue

            # 有序列表
            if self._ORDERED_LIST_RE.match(line):
                items = []
                while i < len(lines) and self._ORDERED_LIST_RE.match(lines[i]):
                    m = self._ORDERED_LIST_RE.match(lines[i])
                    if m:
                        items.append(ContentSection(
                            section_type="paragraph",
                            text=m.group(2),
                        ))
                    i += 1
                sections.append(ContentSection(
                    section_type="list",
                    children=items,
                    metadata={"list_type": "ordered"},
                ))
                continue

            # 普通段落（合并连续非空行）
            para_lines: List[str] = []
            while i < len(lines) and lines[i].strip():
                # 如果遇到其他块级元素的起始，停止
                if (self._HEADING_RE.match(lines[i]) or
                    self._CODE_FENCE_RE.match(lines[i].strip()) or
                    self._BLOCKQUOTE_RE.match(lines[i]) or
                    self._UNORDERED_LIST_RE.match(lines[i]) or
                    self._ORDERED_LIST_RE.match(lines[i]) or
                    self._DIVIDER_RE.match(lines[i].strip())):
                    break
                para_lines.append(lines[i])
                i += 1

            if para_lines:
                sections.append(ContentSection(
                    section_type="paragraph",
                    text="\n".join(para_lines),
                ))

        return sections

    def _extract_images(self, text: str) -> List[ImageRef]:
        """从文本中提取所有图片引用."""
        images: List[ImageRef] = []
        for m in self._IMAGE_RE.finditer(text):
            images.append(ImageRef(
                src=m.group(2),
                alt=m.group(1),
                title=m.group(3) or "",
            ))
        return images
