"""草稿管理器测试模块."""

import json
import os
import tempfile

import pytest

from src.draft.draft_manager import ContentDraft, Draft, DraftManager


@pytest.fixture
def temp_dir():
    """创建临时目录."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def manager(temp_dir):
    """创建草稿管理器实例."""
    drafts_dir = os.path.join(temp_dir, "drafts")
    return DraftManager(drafts_dir=drafts_dir)


class TestContentDraft:
    """内容草稿测试."""

    def test_default_values(self):
        """测试默认值."""
        content = ContentDraft()
        assert content.title == ""
        assert content.content == ""
        assert content.tags == []
        assert content.category == ""

    def test_custom_values(self):
        """测试自定义值."""
        content = ContentDraft(
            title="标题",
            content="内容",
            tags=["Python", "教程"],
            category="技术",
        )
        assert content.title == "标题"
        assert content.tags == ["Python", "教程"]


class TestDraft:
    """草稿测试."""

    def test_auto_id(self):
        """测试自动生成ID."""
        draft = Draft()
        assert draft.id != ""
        assert len(draft.id) == 8

    def test_auto_timestamps(self):
        """测试自动生成时间戳."""
        draft = Draft()
        assert draft.created_at != ""
        assert draft.updated_at != ""
        assert draft.created_at == draft.updated_at

    def test_custom_values(self):
        """测试自定义值."""
        draft = Draft(
            id="test1234",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            content=ContentDraft(title="测试"),
            version=5,
        )
        assert draft.id == "test1234"
        assert draft.version == 5


class TestNewDraft:
    """创建草稿测试."""

    def test_new_empty_draft(self, manager):
        """测试创建空草稿."""
        draft = manager.new_draft()
        assert draft.id != ""
        assert draft.content.title == ""
        assert manager.current_draft is draft

    def test_new_draft_with_content(self, manager):
        """测试创建带内容的草稿."""
        draft = manager.new_draft(
            title="测试文章",
            content="# 标题\n\n内容",
            tags=["Python"],
            category="技术",
        )
        assert draft.content.title == "测试文章"
        assert draft.content.tags == ["Python"]

    def test_new_draft_with_media(self, manager):
        """测试创建带媒体的草稿."""
        media = [{"path": "image.jpg", "caption": "图片"}]
        draft = manager.new_draft(media_items=media)
        assert len(draft.media_items) == 1


class TestSaveAndLoad:
    """保存和加载测试."""

    def test_save_current(self, manager):
        """测试保存当前草稿."""
        draft = manager.new_draft(title="测试")
        draft_id = manager.save_current()
        assert draft_id == draft.id
        assert draft.version == 2  # 保存后版本+1

    def test_save_no_draft(self, manager):
        """测试没有草稿时保存."""
        with pytest.raises(ValueError, match="没有草稿可保存"):
            manager.save_current()

    def test_save_specific_draft(self, manager):
        """测试保存指定草稿."""
        draft = manager.new_draft(title="测试")
        draft_id = manager.save_current(draft)
        assert draft_id == draft.id

    def test_load_draft(self, manager):
        """测试加载草稿."""
        original = manager.new_draft(title="测试标题", content="测试内容")
        manager.save_current()

        loaded = manager.load_draft(original.id)
        assert loaded.id == original.id
        assert loaded.content.title == "测试标题"
        assert loaded.content.content == "测试内容"

    def test_load_nonexistent(self, manager):
        """测试加载不存在的草稿."""
        with pytest.raises(FileNotFoundError):
            manager.load_draft("nonexistent")


class TestListDrafts:
    """列出草稿测试."""

    def test_list_empty(self, manager):
        """测试空列表."""
        drafts = manager.list_drafts()
        assert drafts == []

    def test_list_multiple(self, manager):
        """测试列出多个草稿."""
        manager.new_draft(title="草稿1")
        manager.save_current()
        manager.new_draft(title="草稿2")
        manager.save_current()

        drafts = manager.list_drafts()
        assert len(drafts) == 2

    def test_list_sort_by_title(self, manager):
        """测试按标题排序."""
        manager.new_draft(title="Z草稿")
        manager.save_current()
        manager.new_draft(title="A草稿")
        manager.save_current()

        drafts = manager.list_drafts(sort_by="title")
        assert drafts[0]["title"] == "A草稿"


class TestDeleteDraft:
    """删除草稿测试."""

    def test_delete_draft(self, manager):
        """测试删除草稿."""
        draft = manager.new_draft(title="待删除")
        manager.save_current()

        result = manager.delete_draft(draft.id)
        assert result is True
        assert manager.get_draft_count() == 0

    def test_delete_clears_current(self, manager):
        """测试删除清除当前草稿."""
        draft = manager.new_draft()
        manager.save_current()

        manager.delete_draft(draft.id)
        assert manager.current_draft is None


class TestExport:
    """导出测试."""

    def test_export_basic(self, manager, temp_dir):
        """测试基本导出."""
        manager.new_draft(title="测试标题", content="测试内容")
        manager.save_current()

        output_path = os.path.join(temp_dir, "output.md")
        result = manager.export(manager.current_draft.id, output_path)

        assert os.path.exists(result)
        with open(result, "r", encoding="utf-8") as f:
            content = f.read()
        assert "# 测试标题" in content
        assert "测试内容" in content

    def test_export_with_tags(self, manager, temp_dir):
        """测试带标签导出."""
        manager.new_draft(
            title="标题",
            content="内容",
            tags=["Python", "教程"],
            category="技术",
        )
        manager.save_current()

        output_path = os.path.join(temp_dir, "output.md")
        manager.export(manager.current_draft.id, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "分类: 技术" in content
        assert "Python" in content

    def test_export_with_media(self, manager, temp_dir):
        """测试带媒体导出."""
        media = [{"path": "image.jpg", "caption": "图片说明"}]
        manager.new_draft(title="标题", media_items=media)
        manager.save_current()

        output_path = os.path.join(temp_dir, "output.md")
        manager.export(manager.current_draft.id, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "附件" in content
        assert "image.jpg" in content


class TestDuplicateDraft:
    """复制草稿测试."""

    def test_duplicate(self, manager):
        """测试复制草稿."""
        original = manager.new_draft(
            title="原始标题",
            content="原始内容",
            tags=["tag1"],
        )
        manager.save_current()

        duplicate = manager.duplicate_draft(original.id)
        assert duplicate.id != original.id
        assert "副本" in duplicate.content.title
        assert duplicate.content.content == "原始内容"
        assert duplicate.version == 1


class TestSearchDrafts:
    """搜索草稿测试."""

    def test_search_found(self, manager):
        """测试搜索到结果."""
        manager.new_draft(title="Python教程")
        manager.save_current()
        manager.new_draft(title="Java入门")
        manager.save_current()

        results = manager.search_drafts("Python")
        assert len(results) == 1
        assert "Python" in results[0]["title"]

    def test_search_case_insensitive(self, manager):
        """测试大小写不敏感搜索."""
        manager.new_draft(title="PYTHON教程")
        manager.save_current()

        results = manager.search_drafts("python")
        assert len(results) == 1

    def test_search_not_found(self, manager):
        """测试搜索无结果."""
        manager.new_draft(title="测试")
        manager.save_current()

        results = manager.search_drafts("不存在")
        assert len(results) == 0


class TestDraftCount:
    """草稿数量测试."""

    def test_empty_count(self, manager):
        """测试空数量."""
        assert manager.get_draft_count() == 0

    def test_count_after_add(self, manager):
        """测试添加后数量."""
        manager.new_draft()
        manager.save_current()
        manager.new_draft()
        manager.save_current()
        assert manager.get_draft_count() == 2
