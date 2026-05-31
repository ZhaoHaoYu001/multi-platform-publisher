import pytest
from src.adapters.weibo_adapter import WeiboAdapter
from src.adapters.base_adapter import AdaptationResult
from src.core.content_document import ContentDocument, ContentSection
from src.core.platform_base import PublishMode, PublishResult
from src.core.rule_engine import RuleEngine
import os
RULES_DIR = os.path.join(os.path.dirname(__file__), '..', 'config', 'rules')

class TestWeiboAdapter:
    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)
        self.adapter = WeiboAdapter(self.engine, credentials={'cookie': 'test'})
    def test_platform_name(self): assert self.adapter.platform_name == 'weibo'
    def test_adapt(self):
        doc = ContentDocument(title='t', body=[ContentSection(section_type='paragraph', text='c')])
        r = self.adapter.adapt(doc); assert r.title is not None
    def test_simulate(self):
        doc = ContentDocument(title='t', body=[ContentSection(section_type='paragraph', text='c')])
        r = self.adapter.publish(doc, [], PublishMode.SIMULATE)
        assert r.success and r.platform == 'weibo'
    def test_deliver_no_creds(self):
        r = self.adapter.deliver(AdaptationResult(title='t', content='c'), [])
        assert isinstance(r, PublishResult)
