"""草稿管理器模块.

本模块提供了草稿的创建、保存、加载、删除和导出功能。
"""

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ContentDraft:
    """内容草稿数据类.

    Attributes:
        title: 文章标题
        content: 文章内容（Markdown格式）
        tags: 标签列表
        category: 分类
    """

    title: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = ""


@dataclass
class Draft:
    """草稿数据类.

    Attributes:
        id: 草稿唯一ID
        created_at: 创建时间（ISO格式）
        updated_at: 更新时间（ISO格式）
        content: 内容草稿
        media_items: 媒体项列表
        version: 版本号
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    content: ContentDraft = field(default_factory=ContentDraft)
    media_items: List[Dict] = field(default_factory=list)
    version: int = 1

    def __post_init__(self) -> None:
        """初始化后处理."""
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class DraftManager:
    """草稿管理器，提供草稿的增删改查功能.

    使用示例:
        manager = DraftManager("./drafts")

        # 创建新草稿
        draft = manager.new_draft(
            title="我的文章",
            content="# 标题\n\n内容",
            tags=["Python", "教程"]
        )

        # 保存草稿
        manager.save_current(draft)

        # 加载草稿
        loaded = manager.load_draft(draft.id)

        # 列出所有草稿
        drafts = manager.list_drafts()

        # 导出为Markdown
        manager.export(draft.id, "output.md")
    """

    def __init__(self, drafts_dir: str = "./drafts") -> None:
        """初始化草稿管理器.

        Args:
            drafts_dir: 草稿存储目录
        """
        self._drafts_dir = drafts_dir
        self._index_file = os.path.join(drafts_dir, "index.json")
        self._current_draft: Optional[Draft] = None

        # 确保目录存在
        os.makedirs(drafts_dir, exist_ok=True)

        # 初始化索引
        if not os.path.exists(self._index_file):
            self._save_index({})

    @property
    def drafts_dir(self) -> str:
        """获取草稿目录路径."""
        return self._drafts_dir

    @property
    def current_draft(self) -> Optional[Draft]:
        """获取当前草稿."""
        return self._current_draft

    def _save_index(self, index: Dict) -> None:
        """保存草稿索引.

        Args:
            index: 索引字典
        """
        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _load_index(self) -> Dict:
        """加载草稿索引.

        Returns:
            索引字典
        """
        try:
            with open(self._index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _get_draft_path(self, draft_id: str) -> str:
        """获取草稿文件路径.

        Args:
            draft_id: 草稿ID

        Returns:
            草稿文件路径
        """
        return os.path.join(self._drafts_dir, f"{draft_id}.json")

    def new_draft(
        self,
        title: str = "",
        content: str = "",
        tags: Optional[List[str]] = None,
        category: str = "",
        media_items: Optional[List[Dict]] = None,
    ) -> Draft:
        """创建新草稿.

        Args:
            title: 文章标题
            content: 文章内容
            tags: 标签列表
            category: 分类
            media_items: 媒体项列表

        Returns:
            创建的Draft对象
        """
        now = datetime.now().isoformat()

        draft = Draft(
            id=str(uuid.uuid4())[:8],
            created_at=now,
            updated_at=now,
            content=ContentDraft(
                title=title,
                content=content,
                tags=tags or [],
                category=category,
            ),
            media_items=media_items or [],
            version=1,
        )

        self._current_draft = draft
        return draft

    def save_current(self, draft: Optional[Draft] = None) -> str:
        """保存草稿.

        Args:
            draft: 要保存的草稿，None则保存当前草稿

        Returns:
            草稿ID

        Raises:
            ValueError: 没有草稿可保存时抛出
        """
        draft = draft or self._current_draft
        if draft is None:
            raise ValueError("没有草稿可保存，请先创建草稿")

        # 更新时间
        draft.updated_at = datetime.now().isoformat()
        draft.version += 1

        # 保存草稿文件
        draft_path = self._get_draft_path(draft.id)
        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(asdict(draft), f, ensure_ascii=False, indent=2)

        # 更新索引
        index = self._load_index()
        index[draft.id] = {
            "id": draft.id,
            "title": draft.content.title,
            "created_at": draft.created_at,
            "updated_at": draft.updated_at,
            "version": draft.version,
        }
        self._save_index(index)

        self._current_draft = draft
        return draft.id

    def load_draft(self, draft_id: str) -> Draft:
        """加载草稿.

        Args:
            draft_id: 草稿ID

        Returns:
            加载的Draft对象

        Raises:
            FileNotFoundError: 草稿不存在时抛出
        """
        draft_path = self._get_draft_path(draft_id)
        if not os.path.exists(draft_path):
            raise FileNotFoundError(f"草稿不存在: {draft_id}")

        with open(draft_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 重建对象
        content_data = data.get("content", {})
        draft = Draft(
            id=data["id"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            content=ContentDraft(
                title=content_data.get("title", ""),
                content=content_data.get("content", ""),
                tags=content_data.get("tags", []),
                category=content_data.get("category", ""),
            ),
            media_items=data.get("media_items", []),
            version=data.get("version", 1),
        )

        self._current_draft = draft
        return draft

    def list_drafts(self, sort_by: str = "updated_at") -> List[Dict]:
        """列出所有草稿.

        Args:
            sort_by: 排序字段（updated_at/created_at/title）

        Returns:
            草稿摘要列表
        """
        index = self._load_index()
        drafts = list(index.values())

        # 排序
        if sort_by in ("updated_at", "created_at"):
            drafts.sort(key=lambda x: x.get(sort_by, ""), reverse=True)
        elif sort_by == "title":
            drafts.sort(key=lambda x: x.get("title", ""))

        return drafts

    def delete_draft(self, draft_id: str) -> bool:
        """删除草稿.

        Args:
            draft_id: 草稿ID

        Returns:
            是否成功删除
        """
        draft_path = self._get_draft_path(draft_id)

        # 删除文件
        if os.path.exists(draft_path):
            os.remove(draft_path)

        # 更新索引
        index = self._load_index()
        if draft_id in index:
            del index[draft_id]
            self._save_index(index)

        # 清除当前草稿引用
        if self._current_draft and self._current_draft.id == draft_id:
            self._current_draft = None

        return True

    def export(self, draft_id: str, output_path: str) -> str:
        """导出草稿为Markdown文件.

        Args:
            draft_id: 草稿ID
            output_path: 输出文件路径

        Returns:
            输出文件路径
        """
        draft = self.load_draft(draft_id)

        # 构建Markdown内容
        lines = []

        # 标题
        if draft.content.title:
            lines.append(f"# {draft.content.title}")
            lines.append("")

        # 元数据
        if draft.content.category or draft.content.tags:
            meta_parts = []
            if draft.content.category:
                meta_parts.append(f"分类: {draft.content.category}")
            if draft.content.tags:
                meta_parts.append(f"标签: {', '.join(draft.content.tags)}")
            lines.append(f"> {' | '.join(meta_parts)}")
            lines.append("")

        # 分隔线
        lines.append("---")
        lines.append("")

        # 正文
        lines.append(draft.content.content)
        lines.append("")

        # 媒体项
        if draft.media_items:
            lines.append("---")
            lines.append("")
            lines.append("## 附件")
            lines.append("")
            for i, item in enumerate(draft.media_items, 1):
                path = item.get("path", "")
                caption = item.get("caption", "")
                if caption:
                    lines.append(f"{i}. {path} - {caption}")
                else:
                    lines.append(f"{i}. {path}")

        # 写入文件
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_path

    def duplicate_draft(self, draft_id: str) -> Draft:
        """复制草稿.

        Args:
            draft_id: 要复制的草稿ID

        Returns:
            新的Draft对象
        """
        original = self.load_draft(draft_id)

        now = datetime.now().isoformat()
        new_draft = Draft(
            id=str(uuid.uuid4())[:8],
            created_at=now,
            updated_at=now,
            content=ContentDraft(
                title=f"{original.content.title} (副本)",
                content=original.content.content,
                tags=original.content.tags.copy(),
                category=original.content.category,
            ),
            media_items=[item.copy() for item in original.media_items],
            version=1,
        )

        self._current_draft = new_draft
        return new_draft

    def search_drafts(self, keyword: str) -> List[Dict]:
        """搜索草稿.

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的草稿摘要列表
        """
        index = self._load_index()
        keyword_lower = keyword.lower()

        results = []
        for draft_info in index.values():
            title = draft_info.get("title", "").lower()
            if keyword_lower in title:
                results.append(draft_info)

        return results

    def get_draft_count(self) -> int:
        """获取草稿总数.

        Returns:
            草稿数量
        """
        index = self._load_index()
        return len(index)
