"""凭证管理器测试."""
import os
import pytest
from src.core.credential_store import CredentialStore, PLATFORM_CREDENTIAL_KEYS


class TestCredentialStore:
    """CredentialStore 测试."""

    def setup_method(self):
        self.store = CredentialStore()

    def test_list_platforms(self):
        platforms = self.store.list_platforms()
        assert "wechat" in platforms
        assert "zhihu" in platforms
        assert "bilibili" in platforms
        assert "xiaohongshu" in platforms
        assert "douyin" in platforms
        assert "weibo" in platforms

    def test_get_empty_credentials(self):
        creds = self.store.get("wechat")
        assert isinstance(creds, dict)
        assert "app_id" in creds
        assert "app_secret" in creds

    def test_set_and_get_key(self):
        self.store.set("wechat", "app_id", "test_id")
        assert self.store.get_key("wechat", "app_id") == "test_id"

    def test_is_platform_ready_with_credentials(self):
        self.store.set("wechat", "app_id", "test_id")
        self.store.set("wechat", "app_secret", "test_secret")
        assert self.store.is_platform_ready("wechat") is True

    def test_is_platform_ready_without_credentials(self):
        assert self.store.is_platform_ready("wechat") is False

    def test_is_platform_ready_partial(self):
        self.store.set("wechat", "app_id", "test_id")
        assert self.store.is_platform_ready("wechat") is False

    def test_get_platform_status(self):
        self.store.set("wechat", "app_id", "test_id")
        status = self.store.get_platform_status("wechat")
        assert status["app_id"] is True
        assert status["app_secret"] is False

    def test_get_all_status(self):
        status = self.store.get_all_status()
        assert "wechat" in status
        assert "zhihu" in status
        assert "douyin" in status
        assert "weibo" in status

    def test_list_ready_platforms(self):
        self.store.set("wechat", "app_id", "test_id")
        self.store.set("wechat", "app_secret", "test_secret")
        ready = self.store.list_ready_platforms()
        assert "wechat" in ready
        assert "zhihu" not in ready

    def test_has_any_credentials_empty(self):
        assert self.store.has_any_credentials() is False

    def test_has_any_credentials_with_value(self):
        self.store.set("wechat", "app_id", "test_id")
        assert self.store.has_any_credentials() is True

    def test_clear(self):
        self.store.set("wechat", "app_id", "test_id")
        self.store.clear()
        assert self.store.get_key("wechat", "app_id") == ""

    def test_repr(self):
        r = repr(self.store)
        assert "CredentialStore" in r

    def test_platform_credential_keys_coverage(self):
        """确保所有平台都有凭证键定义."""
        assert "wechat" in PLATFORM_CREDENTIAL_KEYS
        assert "douyin" in PLATFORM_CREDENTIAL_KEYS
        assert "weibo" in PLATFORM_CREDENTIAL_KEYS
