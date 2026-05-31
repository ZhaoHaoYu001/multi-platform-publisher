import pytest
from src.adapters.xiaohongshu_adapter import XiaohongshuAdapter
from src.adapters.base_adapter import AdaptationResult
from src.core.content_document import ContentDocument, ContentSection
from src.core.platform_base import PublishMode, PublishResult
from src.core.rule_engine import RuleEngine
import os
RULES_DIR = os.path.join(os.path.dirname(__file__), '..', 'config', 'rules')

class TestXiaohongshuAdapter:
    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)
        self.adapter = XiaohongshuAdapter(self.engine, credentials={})
    def test_platform_name(self): assert self.adapter.platform_name == 'xiaohongshu'
    def test_adapt_title(self):
        doc = ContentDocument(title='x'*100, body=[ContentSection(section_type='paragraph', text='c')])
        assert len(self.adapter.adapt(doc).title) <= 20
    def test_simulate(self):
        doc = ContentDocument(title='t', body=[ContentSection(section_type='paragraph', text='c')])
        r = self.adapter.publish(doc, [], PublishMode.SIMULATE)
        assert r.success and r.platform == 'xiaohongshu'
    def test_deliver_no_creds(self):
        r = self.adapter.deliver(AdaptationResult(title='t', content='c'), [])
        assert isinstance(r, PublishResult)
    def test_init_cookie(self):
        a = XiaohongshuAdapter(self.engine, {'cookie': 'c'})
        assert a._credentials.get('cookie') == 'c'
