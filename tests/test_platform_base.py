import pytest
from datetime import datetime
from src.core.platform_base import PublishMode, PublishResult

class TestPublishMode:
    def test_simulate(self): assert PublishMode.SIMULATE.value == 'simulate'
    def test_real(self): assert PublishMode.REAL.value == 'real'
    def test_ne(self): assert PublishMode.SIMULATE != PublishMode.REAL

class TestPublishResult:
    def test_success(self):
        r = PublishResult(success=True, platform='test', message='ok', url='http://x')
        assert r.success and r.platform == 'test'
    def test_failure(self):
        r = PublishResult(success=False, platform='test', message='fail')
        assert not r.success
    def test_default_time(self):
        r = PublishResult(success=True, platform='t', message='m')
        assert isinstance(r.published_at, datetime)
    def test_str_ok(self):
        assert '[OK]' in str(PublishResult(True, 't', 'm'))
    def test_str_fail(self):
        assert '[FAIL]' in str(PublishResult(False, 't', 'm'))
    def test_optional_fields(self):
        r = PublishResult(True, 't', 'm')
        assert r.url is None and r.raw_response is None
    def test_raw_response(self):
        r = PublishResult(True, 't', 'm', raw_response={'k': 'v'})
        assert r.raw_response['k'] == 'v'
