import os
from unittest.mock import patch
import pytest
from app import run_cli, run_web
from publish import init_registry, load_content, load_images
from src.core.platform_base import PublishMode

class TestLoadContent:
    def test_string(self): assert load_content("direct", "") == "direct"
    def test_file(self, tmp_path):
        f = tmp_path / "t.md"; f.write_text("# test", encoding="utf-8")
        assert "test" in load_content("", str(f))
    def test_file_priority(self, tmp_path):
        f = tmp_path / "t.md"; f.write_text("file", encoding="utf-8")
        assert load_content("direct", str(f)) == "file"
    def test_missing(self):
        with pytest.raises(SystemExit): load_content("", "nofile.md")

class TestLoadImages:
    def test_existing(self, tmp_path):
        f = tmp_path / "i.jpg"; f.write_text("x")
        assert len(load_images([str(f)])) == 1
    def test_missing(self, tmp_path):
        f = tmp_path / "i.jpg"; f.write_text("x")
        assert len(load_images([str(f), "no.jpg"])) == 1
    def test_empty(self): assert load_images([]) == []

class TestInitRegistry:
    @patch.dict(os.environ, {}, clear=True)
    def test_all(self):
        r = init_registry(["wechat","zhihu","bilibili","xiaohongshu","douyin","weibo"])
        assert len(r.list_platforms()) == 6
    def test_specific(self):
        r = init_registry(["wechat","zhihu"])
        assert len(r.list_platforms()) == 2
    def test_unknown(self):
        r = init_registry(["unknown"]); assert len(r.list_platforms()) == 0

class TestAppEntry:
    def test_imports(self):
        assert callable(run_web)
        assert callable(run_cli)
