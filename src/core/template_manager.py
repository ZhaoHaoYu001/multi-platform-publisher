"""内容模板管理器.

提供内容模板的加载、变量替换和管理功能。
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ContentTemplate:
    """内容模板.

    Attributes:
        id: 模板唯一ID
        name: 模板名称
        description: 模板描述
        title_template: 标题模板（支持 {{variable}} 变量）
        content_template: 内容模板（支持 {{variable}} 变量）
        variables: 变量列表
        category: 模板分类
        tags: 标签列表
    """

    id: str = ""
    name: str = ""
    description: str = ""
    title_template: str = ""
    content_template: str = ""
    variables: List[str] = field(default_factory=list)
    category: str = ""
    tags: List[str] = field(default_factory=list)


class TemplateManager:
    """内容模板管理器.

    使用示例:
        manager = TemplateManager("config/templates")

        # 列出模板
        templates = manager.list_templates()

        # 获取模板
        tpl = manager.get_template("tech-tutorial")

        # 应用模板（变量替换）
        title, content = manager.apply_template("tech-tutorial", {
            "title": "Python入门",
            "topic": "基础语法",
        })
    """

    def __init__(self, templates_dir: Optional[str] = None) -> None:
        """初始化模板管理器.

        Args:
            templates_dir: 模板文件目录，None 时使用内置模板
        """
        self._templates_dir = templates_dir
        self._templates: Dict[str, ContentTemplate] = {}
        self._loaded = False

    def _load_builtin_templates(self) -> None:
        """加载内置模板."""
        builtin = [
            ContentTemplate(
                id="tech-tutorial",
                name="技术教程",
                description="适用于技术教程类文章",
                category="技术",
                tags=["教程", "技术"],
                title_template="{{title}}：从入门到精通",
                content_template=(
                    "# {{title}}\n\n"
                    "## 前言\n\n在本教程中，我们将学习{{topic}}。\n\n"
                    "## 环境准备\n\n- Python 3.8+\n- pip install {{package}}\n\n"
                    "## 基础用法\n\n```python\n# 示例代码\n{{code_example}}\n```\n\n"
                    "## 进阶技巧\n\n{{advanced_content}}\n\n"
                    "## 总结\n\n{{summary}}\n\n"
                    "> 分类: 技术 | 标签: {{tags}}"
                ),
                variables=["title", "topic", "package", "code_example", "advanced_content", "summary", "tags"],
            ),
            ContentTemplate(
                id="product-review",
                name="产品评测",
                description="适用于产品评测类文章",
                category="评测",
                tags=["评测", "产品"],
                title_template="{{product}} 深度评测：{{verdict}}",
                content_template=(
                    "# {{product}} 深度评测\n\n"
                    "## 产品概述\n\n{{product}}是{{brand}}推出的{{category}}。\n\n"
                    "## 外观设计\n\n{{design_review}}\n\n"
                    "## 功能体验\n\n{{feature_review}}\n\n"
                    "## 优缺点\n\n**优点：**\n{{pros}}\n\n**缺点：**\n{{cons}}\n\n"
                    "## 购买建议\n\n{{recommendation}}\n\n"
                    "> 分类: 评测 | 标签: {{tags}}"
                ),
                variables=["product", "brand", "category", "verdict", "design_review", "feature_review", "pros", "cons", "recommendation", "tags"],
            ),
            ContentTemplate(
                id="daily-share",
                name="日常分享",
                description="适用于日常分享类文章",
                category="生活",
                tags=["生活", "分享"],
                title_template="{{title}}",
                content_template=(
                    "# {{title}}\n\n"
                    "今天{{mood}}，想和大家分享一下{{topic}}。\n\n"
                    "## {{section1_title}}\n\n{{section1_content}}\n\n"
                    "## {{section2_title}}\n\n{{section2_content}}\n\n"
                    "## 写在最后\n\n{{ending}}\n\n"
                    "> 分类: 生活 | 标签: {{tags}}"
                ),
                variables=["title", "mood", "topic", "section1_title", "section1_content", "section2_title", "section2_content", "ending", "tags"],
            ),
            ContentTemplate(
                id="industry-analysis",
                name="行业分析",
                description="适用于行业分析类文章",
                category="行业",
                tags=["行业", "分析"],
                title_template="{{year}}{{industry}}行业{{topic}}分析",
                content_template=(
                    "# {{year}}{{industry}}行业{{topic}}分析\n\n"
                    "## 行业背景\n\n{{background}}\n\n"
                    "## 市场现状\n\n{{market_status}}\n\n"
                    "## 关键趋势\n\n{{trends}}\n\n"
                    "## 竞争格局\n\n{{competition}}\n\n"
                    "## 未来展望\n\n{{outlook}}\n\n"
                    "> 分类: 行业 | 标签: {{tags}}"
                ),
                variables=["year", "industry", "topic", "background", "market_status", "trends", "competition", "outlook", "tags"],
            ),
        ]

        for tpl in builtin:
            self._templates[tpl.id] = tpl

    def _load_from_files(self) -> None:
        """从文件加载模板."""
        if not self._templates_dir or not os.path.exists(self._templates_dir):
            return

        for filename in os.listdir(self._templates_dir):
            if not filename.endswith((".yaml", ".yml")):
                continue

            filepath = os.path.join(self._templates_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                tpl = ContentTemplate(
                    id=data.get("id", filename.replace(".yaml", "").replace(".yml", "")),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    category=data.get("category", ""),
                    tags=data.get("tags", []),
                    title_template=data.get("title_template", ""),
                    content_template=data.get("content_template", ""),
                    variables=data.get("variables", []),
                )
                self._templates[tpl.id] = tpl
            except Exception:
                continue

    def _ensure_loaded(self) -> None:
        """确保模板已加载."""
        if not self._loaded:
            self._load_builtin_templates()
            self._load_from_files()
            self._loaded = True

    def list_templates(self, category: Optional[str] = None) -> List[ContentTemplate]:
        """列出所有模板.

        Args:
            category: 按分类过滤（None 表示全部）

        Returns:
            模板列表
        """
        self._ensure_loaded()

        templates = list(self._templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates

    def get_template(self, template_id: str) -> Optional[ContentTemplate]:
        """获取模板.

        Args:
            template_id: 模板ID

        Returns:
            模板实例，不存在时返回 None
        """
        self._ensure_loaded()
        return self._templates.get(template_id)

    def apply_template(
        self,
        template_id: str,
        variables: Dict[str, str],
    ) -> tuple:
        """应用模板（变量替换）.

        Args:
            template_id: 模板ID
            variables: 变量值字典

        Returns:
            (title, content) 元组

        Raises:
            ValueError: 模板不存在时抛出
        """
        tpl = self.get_template(template_id)
        if tpl is None:
            raise ValueError(f"模板不存在: {template_id}")

        title = tpl.title_template
        content = tpl.content_template

        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            title = title.replace(placeholder, value)
            content = content.replace(placeholder, value)

        return title, content

    def add_template(self, tpl: ContentTemplate) -> None:
        """添加自定义模板.

        Args:
            tpl: 模板实例
        """
        self._ensure_loaded()
        self._templates[tpl.id] = tpl

    def remove_template(self, template_id: str) -> bool:
        """删除模板.

        Args:
            template_id: 模板ID

        Returns:
            是否删除成功
        """
        self._ensure_loaded()
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False

    def list_categories(self) -> List[str]:
        """列出所有分类.

        Returns:
            分类列表
        """
        self._ensure_loaded()
        categories = set()
        for tpl in self._templates.values():
            if tpl.category:
                categories.add(tpl.category)
        return sorted(categories)

    def search_templates(self, keyword: str) -> List[ContentTemplate]:
        """搜索模板.

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的模板列表
        """
        self._ensure_loaded()
        keyword_lower = keyword.lower()
        results = []
        for tpl in self._templates.values():
            if (keyword_lower in tpl.name.lower() or
                keyword_lower in tpl.description.lower() or
                keyword_lower in tpl.category.lower()):
                results.append(tpl)
        return results
