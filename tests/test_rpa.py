import os, sys, tempfile, pytest
from unittest.mock import MagicMock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRPABase:
    def test_init(self):
        from src.rpa.base import RPABase
        class T(RPABase):
            def login(self): return True
            def publish(self, title, content, images, **kw): return {'success': True}
        with tempfile.TemporaryDirectory() as d:
            r = T(platform_name='test', cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            assert r.platform_name == 'test'
    def test_cookie_path(self):
        from src.rpa.base import RPABase
        class T(RPABase):
            def login(self): return True
            def publish(self, title, content, images, **kw): return {'success': True}
        with tempfile.TemporaryDirectory() as d:
            r = T(platform_name='bilibili', cookie_dir=d)
            assert 'bilibili_cookies.json' in r.cookie_file
    def test_profile_path(self):
        from src.rpa.base import RPABase
        class T(RPABase):
            def login(self): return True
            def publish(self, title, content, images, **kw): return {'success': True}
        with tempfile.TemporaryDirectory() as d:
            r = T(platform_name='zhihu', profile_dir=d)
            assert r.profile_path.endswith(os.path.join('zhihu'))
            assert os.path.isdir(r.profile_path)
            assert r.use_persistent_profile is True
    def test_has_login_cookies(self):
        from src.rpa.base import RPABase
        class T(RPABase):
            def login(self): return True
            def publish(self, title, content, images, **kw): return {'success': True}
        class C:
            def cookies(self):
                return [{'name': 'SESSDATA'}]
        r = T(platform_name='bilibili')
        r._context = C()
        assert r.has_login_cookies(['SESSDATA']) is True
        assert r.has_login_cookies(['z_c0']) is False
    def test_context_manager(self):
        from src.rpa.base import RPABase
        class T(RPABase):
            def login(self): return True
            def publish(self, title, content, images, **kw): return {'success': True}
        with tempfile.TemporaryDirectory() as d:
            r = T(platform_name='test', cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            r.launch_browser = MagicMock(return_value=True)
            r.close_browser = MagicMock()
            with r: pass
            r.launch_browser.assert_called_once()

class TestBilibiliRPA:
    def test_init(self):
        from src.rpa.bilibili_rpa import BilibiliRPA
        with tempfile.TemporaryDirectory() as d:
            r = BilibiliRPA(cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            assert r.platform_name == 'bilibili'
    def test_publish_no_browser(self):
        from src.rpa.bilibili_rpa import BilibiliRPA
        with tempfile.TemporaryDirectory() as d:
            r = BilibiliRPA(cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            r.launch_browser = MagicMock(return_value=False)
            assert r.publish(title='t', content='c', images=[])['success'] is False

class TestZhihuRPA:
    def test_init(self):
        from src.rpa.zhihu_rpa import ZhihuRPA
        with tempfile.TemporaryDirectory() as d:
            r = ZhihuRPA(cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            assert r.platform_name == 'zhihu'
    def test_publish_no_browser(self):
        from src.rpa.zhihu_rpa import ZhihuRPA
        with tempfile.TemporaryDirectory() as d:
            r = ZhihuRPA(cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            r.launch_browser = MagicMock(return_value=False)
            assert r.publish(title='t', content='c', images=[])['success'] is False

class TestXiaohongshuRPA:
    def test_init(self):
        from src.rpa.xiaohongshu_rpa import XiaohongshuRPA
        with tempfile.TemporaryDirectory() as d:
            r = XiaohongshuRPA(cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            assert r.platform_name == 'xiaohongshu'
    def test_publish_no_browser(self):
        from src.rpa.xiaohongshu_rpa import XiaohongshuRPA
        with tempfile.TemporaryDirectory() as d:
            r = XiaohongshuRPA(cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            r.launch_browser = MagicMock(return_value=False)
            assert r.publish(title='t', content='c', images=[])['success'] is False

class TestDouyinRPA:
    def test_init(self):
        from src.rpa.douyin_rpa import DouyinRPA
        with tempfile.TemporaryDirectory() as d:
            r = DouyinRPA(platform_name="douyin", cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            assert r.platform_name == 'douyin'

class TestWeiboRPA:
    def test_init(self):
        from src.rpa.weibo_rpa import WeiboRPA
        with tempfile.TemporaryDirectory() as d:
            r = WeiboRPA(platform_name='weibo', cookie_dir=os.path.join(d,'c'), screenshot_dir=os.path.join(d,'s'))
            assert r.platform_name == 'weibo'
