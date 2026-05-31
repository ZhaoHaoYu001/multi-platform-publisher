import pytest
from unittest.mock import MagicMock, patch
from src.adapters.bilibili_adapter import BilibiliAdapter
from src.adapters.base_adapter import AdaptationResult
from src.core.content_document import ContentDocument, ContentSection
from src.core.platform_base import PublishMode, PublishResult
from src.core.rule_engine import RuleEngine
import os
RULES_DIR = os.path.join(os.path.dirname(__file__), '..', 'config', 'rules')

class TestBilibiliAdapter:
    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)
        self.adapter = BilibiliAdapter(self.engine, credentials={})
    def test_platform_name(self): assert self.adapter.platform_name == 'bilibili'
    def test_adapt_title(self):
        doc = ContentDocument(title='test', body=[ContentSection(section_type='paragraph', text='c')])
        r = self.adapter.adapt(doc); assert r.title == 'test'
    def test_adapt_title_long(self):
        doc = ContentDocument(title='x'*200, body=[ContentSection(section_type='paragraph', text='c')])
        r = self.adapter.adapt(doc); assert len(r.title) <= 80
    def test_simulate(self):
        doc = ContentDocument(title='t', body=[ContentSection(section_type='paragraph', text='c')])
        r = self.adapter.publish(doc, [], PublishMode.SIMULATE)
        assert r.success and r.platform == 'bilibili' and '模拟发布' in r.message
    def test_deliver_no_creds(self):
        a = AdaptationResult(title='t', content='c')
        r = self.adapter.deliver(a, []); assert isinstance(r, PublishResult)
    @patch('src.api.bilibili_api.BilibiliAPI')
    def test_deliver_api(self, mock_cls):
        mock_api = MagicMock(); mock_api.publish_article.return_value = {'url': 'http://b'}
        mock_cls.return_value = mock_api
        adapter = BilibiliAdapter(self.engine, {'sess_data': 's', 'csrf': 'c'})
        r = adapter.deliver(AdaptationResult(title='t', content='c'), [])
        assert r.success
    def test_init_creds(self):
        a = BilibiliAdapter(self.engine, {'sess_data': 's', 'csrf': 'c'})
        assert a._credentials.get('sess_data') == 's'
