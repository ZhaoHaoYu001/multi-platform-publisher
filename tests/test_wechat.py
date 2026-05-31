import pytest
from unittest.mock import MagicMock, patch
from src.adapters.wechat_adapter import WechatAdapter
from src.adapters.base_adapter import AdaptationResult
from src.core.content_document import ContentDocument, ContentSection
from src.core.platform_base import PublishMode, PublishResult
from src.core.rule_engine import RuleEngine
import os
RULES_DIR = os.path.join(os.path.dirname(__file__), '..', 'config', 'rules')

class TestWechatAdapter:
    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)
        self.adapter = WechatAdapter(self.engine, credentials={})
    def test_platform_name(self): assert self.adapter.platform_name == 'wechat'
    def test_adapt_title(self):
        doc = ContentDocument(title='t', body=[ContentSection(section_type='paragraph', text='c')])
        assert self.adapter.adapt(doc).title == 't'
    def test_adapt_title_long(self):
        doc = ContentDocument(title='x'*200, body=[ContentSection(section_type='paragraph', text='c')])
        assert len(self.adapter.adapt(doc).title) <= 64
    def test_simulate(self):
        doc = ContentDocument(title='t', body=[ContentSection(section_type='paragraph', text='c')])
        r = self.adapter.publish(doc, [], PublishMode.SIMULATE)
        assert r.success and r.platform == 'wechat'
    def test_deliver_no_creds(self):
        r = self.adapter.deliver(AdaptationResult(title='t', content='c'), [])
        assert isinstance(r, PublishResult)
    @patch('src.api.wechat_api.WechatAPI')
    def test_deliver_api(self, mock_cls):
        mock_api = MagicMock(); mock_api.publish_article.return_value = {'url': 'http://w'}
        mock_cls.return_value = mock_api
        a = WechatAdapter(self.engine, {'app_id': 'id', 'app_secret': 's'})
        assert a.deliver(AdaptationResult(title='t', content='c'), []).success
    def test_init_creds(self):
        a = WechatAdapter(self.engine, {'app_id': 'id', 'app_secret': 's'})
        assert a._credentials.get('app_id') == 'id'
