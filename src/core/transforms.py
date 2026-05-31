"""
Content transformation utilities for multi-platform publishing.

Provides a ContentTransforms class with static methods for converting
content between different formats (Markdown, HTML, BBCode, plain text)
and adding platform-specific decorations.
"""

import re


class ContentTransforms:
    """Static methods for content transformation across publishing platforms."""

    @staticmethod
    def heading_to_html(text: str, mapping: dict) -> str:
        """Convert Markdown headings to HTML tags.

        Args:
            text: Input text with Markdown headings (e.g., "# Title").
            mapping: Dict mapping heading level to HTML tag name,
                     e.g., {1: "h1", 2: "h2", 3: "h3"}.

        Returns:
            Text with headings replaced by HTML tags.
        """
        def replace_heading(match):
            level = len(match.group(1))
            content = match.group(2).strip()
            tag = mapping.get(level)
            if tag:
                return f"<{tag}>{content}</{tag}>"
            return match.group(0)

        return re.sub(r'^(#{1,6})\s+(.+)$', replace_heading, text, flags=re.MULTILINE)

    @staticmethod
    def heading_to_bold(text: str) -> str:
        """Convert Markdown headings to bold text.

        Args:
            text: Input text with Markdown headings.

        Returns:
            Text with headings converted to **bold** format.
        """
        return re.sub(r'^#{1,6}\s+(.+)$', r'**\1**', text, flags=re.MULTILINE)

    @staticmethod
    def bold_to_strong(text: str) -> str:
        """Convert Markdown bold to HTML strong tags.

        Args:
            text: Input text with **bold** syntax.

        Returns:
            Text with <strong> tags replacing bold markers.
        """
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    @staticmethod
    def italic_to_em(text: str) -> str:
        """Convert Markdown italic to HTML em tags.

        Args:
            text: Input text with *italic* syntax.

        Returns:
            Text with <em> tags replacing italic markers.
        """
        return re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

    @staticmethod
    def code_to_code_tag(text: str) -> str:
        """Convert inline Markdown code to HTML code tags.

        Args:
            text: Input text with `code` syntax.

        Returns:
            Text with <code> tags replacing backtick markers.
        """
        return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    @staticmethod
    def blockquote_to_html(text: str) -> str:
        """Convert Markdown blockquotes to HTML blockquote tags.

        Args:
            text: Input text with > quote syntax.

        Returns:
            Text with <blockquote> tags replacing quote markers.
        """
        lines = text.split('\n')
        result = []
        in_blockquote = False
        quote_lines = []

        for line in lines:
            if line.startswith('> '):
                quote_lines.append(line[2:])
                in_blockquote = True
            elif in_blockquote and line.strip() == '':
                result.append('<blockquote>' + '\n'.join(quote_lines) + '</blockquote>')
                quote_lines = []
                in_blockquote = False
            else:
                if in_blockquote:
                    result.append('<blockquote>' + '\n'.join(quote_lines) + '</blockquote>')
                    quote_lines = []
                    in_blockquote = False
                result.append(line)

        if quote_lines:
            result.append('<blockquote>' + '\n'.join(quote_lines) + '</blockquote>')

        return '\n'.join(result)

    @staticmethod
    def wrap_paragraphs(text: str) -> str:
        """Wrap text blocks separated by blank lines in <p> tags.

        Args:
            text: Input text with paragraph breaks.

        Returns:
            Text with paragraphs wrapped in <p> tags.
        """
        blocks = re.split(r'\n\s*\n', text.strip())
        wrapped = []
        for block in blocks:
            stripped = block.strip()
            if stripped:
                wrapped.append(f'<p>{stripped}</p>')
        return '\n\n'.join(wrapped)

    @staticmethod
    def markdown_to_bbcode(text: str) -> str:
        """Convert Markdown to BBCode format.

        Converts headings, bold, italic, strikethrough, inline code,
        code blocks, quotes, lists, images, links, and horizontal rules.

        Args:
            text: Input text in Markdown format.

        Returns:
            Text converted to BBCode format.
        """
        result = text

        # Headings: # -> [h1], ## -> [h2], ### -> [h3]
        for level in range(6, 0, -1):
            pattern = r'^' + r'#' * level + r'\s+(.+)$'
            replacement = f'[h{level}]\\1[/h{level}]'
            result = re.sub(pattern, replacement, result, flags=re.MULTILINE)

        # Bold: **text** -> [b]text[/b]
        result = re.sub(r'\*\*(.+?)\*\*', r'[b]\1[/b]', result)

        # Strikethrough: ~~text~~ -> [s]text[/s]
        result = re.sub(r'~~(.+?)~~', r'[s]\1[/s]', result)

        # Italic: *text* -> [i]text[/i]
        result = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'[i]\1[/i]', result)

        # Code blocks: ```lang\ncode\n``` -> [code]code[/code]
        result = re.sub(r'```\w*\n(.*?)```', r'[code]\1[/code]', result, flags=re.DOTALL)

        # Inline code: `text` -> [code]text[/code]
        result = re.sub(r'`([^`]+)`', r'[code]\1[/code]', result)

        # Blockquotes: > text -> [quote]text[/quote]
        result = re.sub(r'^>\s+(.+)$', r'[quote]\1[/quote]', result, flags=re.MULTILINE)

        # Unordered lists: - text -> [*] text
        result = re.sub(r'^[\-\*]\s+(.+)$', r'[*] \1', result, flags=re.MULTILINE)

        # Ordered lists: 1. text -> [*] text (simplified)
        result = re.sub(r'^\d+\.\s+(.+)$', r'[*] \1', result, flags=re.MULTILINE)

        # Images: ![alt](url) -> [img]url[/img]
        result = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'[img]\2[/img]', result)

        # Links: [text](url) -> [url=link]text[/url]
        result = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[url=\2]\1[/url]', result)

        # Horizontal rules: --- -> [hr]
        result = re.sub(r'^-{3,}$', r'[hr]', result, flags=re.MULTILINE)

        return result

    @staticmethod
    def markdown_to_plain(text: str) -> str:
        """Strip all Markdown syntax and return plain text.

        Args:
            text: Input text in Markdown format.

        Returns:
            Plain text with all Markdown formatting removed.
        """
        result = text

        # Remove headings: # Title -> Title
        result = re.sub(r'^#{1,6}\s+', '', result, flags=re.MULTILINE)

        # Remove bold: **text** -> text
        result = re.sub(r'\*\*(.+?)\*\*', r'\1', result)

        # Remove strikethrough: ~~text~~ -> text
        result = re.sub(r'~~(.+?)~~', r'\1', result)

        # Remove italic: *text* -> text
        result = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', result)

        # Remove inline code: `text` -> text
        result = re.sub(r'`([^`]+)`', r'\1', result)

        # Remove code blocks: ```lang\ncode\n``` -> code
        result = re.sub(r'```\w*\n(.*?)```', r'\1', result, flags=re.DOTALL)

        # Remove blockquotes: > text -> text
        result = re.sub(r'^>\s+', '', result, flags=re.MULTILINE)

        # Remove images: ![alt](url) -> alt
        result = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', result)

        # Remove links: [text](url) -> text
        result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)

        # Remove list markers: - text -> text
        result = re.sub(r'^[\-\*]\s+', '', result, flags=re.MULTILINE)

        # Remove ordered list markers: 1. text -> text
        result = re.sub(r'^\d+\.\s+', '', result, flags=re.MULTILINE)

        # Remove horizontal rules
        result = re.sub(r'^-{3,}$', '', result, flags=re.MULTILINE)

        return result

    @staticmethod
    def add_emoji_decorations(text: str, emoji_map: dict) -> str:
        """Add emoji prefix to lines matching keywords.

        Args:
            text: Input text to decorate.
            emoji_map: Dict mapping keywords to emoji, e.g., {"推荐": "👍", "教程": "📚"}.

        Returns:
            Text with emoji prefixes added to matching lines.
        """
        lines = text.split('\n')
        result = []
        for line in lines:
            for keyword, emoji in emoji_map.items():
                if keyword in line:
                    line = f'{emoji} {line}'
                    break
            result.append(line)
        return '\n'.join(result)

    @staticmethod
    def add_hashtags(text: str, keywords: list = None, max_tags: int = 3) -> str:
        """Append hashtag keywords at the end of text.

        Args:
            text: Input text.
            keywords: List of keyword strings. Defaults to ["分享", "推荐"].
            max_tags: Maximum number of tags to add (default 3).

        Returns:
            Text with hashtags appended at the end.
        """
        if keywords is None:
            keywords = ["分享", "推荐"]
        tags = [f'#{kw}#' for kw in keywords[:max_tags]]
        return text.rstrip() + '\n\n' + ' '.join(tags)

    @staticmethod
    def add_salt_marks(text: str) -> str:
        """Add Zhihu-style salt marks (invite prefix and summary label).

        Args:
            text: Input text.

        Returns:
            Text with "谢邀" prefix and "总结" label added.
        """
        return f'谢邀，\n\n{text}\n\n总结：'

    @staticmethod
    def add_code_language_annotation(text: str) -> str:
        """Add 'text' language to bare code blocks without language annotation.

        Args:
            text: Input text with Markdown code blocks.

        Returns:
            Text where bare ``` are replaced with ```text.
        """
        # Match ``` that is not followed by a language identifier (end of line)
        return re.sub(r'^```\s*$', '```text', text, flags=re.MULTILINE)

    @staticmethod
    def strip_code_language(text: str) -> str:
        """Remove language annotation from code blocks.

        Args:
            text: Input text with annotated code blocks (e.g., ```python).

        Returns:
            Text where ```language is replaced with bare ```.
        """
        return re.sub(r'^```\w+\s*$', '```', text, flags=re.MULTILINE)

    @staticmethod
    def divider_to_dash(text: str) -> str:
        """Convert Markdown horizontal rules to long dash lines.

        Args:
            text: Input text with --- dividers.

        Returns:
            Text with --- replaced by long dashes.
        """
        return re.sub(r'^-{3,}$', '——————', text, flags=re.MULTILINE)

    @staticmethod
    def add_interaction_prompt(text: str) -> str:
        """Add a casual interaction prompt at the end of text.

        Args:
            text: Input text.

        Returns:
            Text with an interaction prompt appended.
        """
        return text.rstrip() + '\n\n觉得有用的话点个赞吧~'

    @staticmethod
    def add_original_declaration(text: str) -> str:
        """Add an original content declaration at the end of text.

        Args:
            text: Input text.

        Returns:
            Text with original content declaration appended.
        """
        return text.rstrip() + '\n\n本文为原创内容，转载请注明出处。'
