import pytest
from src.adapters.zhihu_adapter import ZhihuAdapter
from src.adapters.base_adapter import AdaptationResult
from src.core.content_document import ContentDocument, ContentSection
from src.core.platform_base import PublishMode, PublishResult
from src.core.rule_engine import RuleEngine
import os
RULES_DIR = os.path.join(os.path.dirname(__file__), '..', 'config', 'rules')

class TestZhihuAdapter:
    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)
        self.adapter = ZhihuAdapter(self.engine, credentials={})
    def test_platform_name(self): assert self.adapter.platform_name == 'zhihu'
    def test_adapt_title(self):
        doc = ContentDocument(title='t', body=[ContentSection(section_type='paragraph', text='c')])
        assert self.adapter.adapt(doc).title == 't'
    def test_adapt_title_long(self):
        doc = ContentDocument(title='x'*200, body=[ContentSection(section_type='paragraph', text='c')])
        assert len(self.adapter.adapt(doc).title) <= 60
    def test_simulate(self):
        doc = ContentDocument(title='t', body=[ContentSection(section_type='paragraph', text='c')])
        r = self.adapter.publish(doc, [], PublishMode.SIMULATE)
        assert r.success and r.platform == 'zhihu'
    def test_deliver_no_creds(self):
        r = self.adapter.deliver(AdaptationResult(title='t', content='c'), [])
        assert isinstance(r, PublishResult)
    def test_init_creds(self):
        a = ZhihuAdapter(self.engine, {'username': 'u', 'password': 'p'})
        assert a._credentials.get('username') == 'u'
