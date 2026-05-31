#!/usr/bin/env python3
import os, sys
from typing import Dict, List, Optional
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.adapters.registry import AdapterRegistry
from src.adapters.wechat_adapter import WechatAdapter
from src.adapters.zhihu_adapter import ZhihuAdapter
from src.adapters.bilibili_adapter import BilibiliAdapter
from src.adapters.xiaohongshu_adapter import XiaohongshuAdapter
from src.adapters.douyin_adapter import DouyinAdapter
from src.adapters.weibo_adapter import WeiboAdapter
from src.core.content_parser import ContentParser
from src.core.credential_store import CredentialStore
from src.core.platform_base import PublishMode
from src.core.rule_engine import RuleEngine
from src.draft.draft_manager import DraftManager
from src.media.media_manager import MediaManager
from src.review.previewer import Previewer

class App:
    def __init__(self):
        self.draft_manager = DraftManager()
        self.media_manager = MediaManager()
        self.previewer = Previewer()
        self.rule_engine = RuleEngine(rules_dir=os.path.join(os.path.dirname(__file__), 'config', 'rules'))
        self.credential_store = CredentialStore()
        self.credential_store.load_from_env()
        self.registry = AdapterRegistry(self.rule_engine)
        for cls in [WechatAdapter, ZhihuAdapter, BilibiliAdapter, XiaohongshuAdapter, DouyinAdapter, WeiboAdapter]:
            self.registry.register(cls.platform_name, cls)
        self.current_title = ''
        self.current_content = ''
        self.current_tags: List[str] = []
        self.current_category = ''

    def _get_adapter(self, name):
        creds = {p: self.credential_store.get(p) for p in self.credential_store.list_platforms()}
        return self.registry.get(name, credentials=creds.get(name, {}))

    def run(self):
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print('=' * 50)
            print('  Multi-Platform Publisher (adapter/pipeline)')
            print('=' * 50)
            platforms = self.registry.list_platforms()
            print(f'Title: {self.current_title or "(not set)"}')
            print(f'Content: {len(self.current_content)} chars')
            print(f'Platforms: {", ".join(platforms)}')
            print('-' * 50)
            print('1.Edit 2.Media 3.Preview 4.Publish 5.Drafts 0.Exit')
            c = input('Choice: ').strip()
            if c == '1': self._edit()
            elif c == '2': self._media()
            elif c == '3': self._preview()
            elif c == '4': self._publish()
            elif c == '5': self._drafts()
            elif c == '0':
                if self.current_title or self.current_content:
                    d = self.draft_manager.new_draft(title=self.current_title, content=self.current_content, tags=self.current_tags, category=self.current_category)
                    self.draft_manager.save_current(d)
                print('Bye!'); break

    def _edit(self):
        t = input('Title: ').strip()
        if t: self.current_title = t
        c = input('Content (empty to skip): ').strip()
        if c: self.current_content = c
        tg = input('Tags (comma): ').strip()
        if tg: self.current_tags = [x.strip() for x in tg.split(',') if x.strip()]

    def _media(self):
        p = input('Image path (empty to skip): ').strip()
        if p and os.path.exists(p):
            self.media_manager.add_image(p)
            print('Added')
        elif p:
            print('Not found')

    def _preview(self):
        if not self.current_title: print('Set title first'); return
        images = [i.path for i in self.media_manager.images]
        try:
            r = self.previewer.generate_all_previews(title=self.current_title, content=self.current_content, images=images, tags=self.current_tags)
            for p, path in r.items(): print(f'  {p}: {path}')
        except Exception as e: print(f'Error: {e}')

    def _publish(self):
        if not self.current_title: print('Set title first'); return
        platforms = self.registry.list_platforms()
        for i, n in enumerate(platforms, 1):
            s = 'Y' if self.credential_store.is_platform_ready(n) else 'N'
            print(f'  {i}. {n} [creds:{s}]')
        print(f'  {len(platforms)+1}. All')
        c = input('Platform: ').strip()
        mc = input('Mode (1=sim 2=real): ').strip()
        mode = PublishMode.REAL if mc == '2' else PublishMode.SIMULATE
        images = [i.path for i in self.media_manager.images]
        parser = ContentParser()
        doc = parser.parse(self.current_content, title=self.current_title, tags=self.current_tags or None)
        results = {}
        if c == str(len(platforms)+1):
            for n in platforms:
                a = self._get_adapter(n)
                results[n] = a.publish(doc, images, mode) if a else None
        else:
            try:
                n = platforms[int(c)-1]
                a = self._get_adapter(n)
                results[n] = a.publish(doc, images, mode) if a else None
            except: print('Invalid'); return
        for n, r in results.items():
            if r: print(f'  {r}')

    def _drafts(self):
        drafts = self.draft_manager.list_drafts()
        for i, d in enumerate(drafts[:5], 1): print(f'  {i}. {d.get("title", "untitled")}')
        print('1.Save 2.Load 0.Back')
        c = input('Choice: ').strip()
        if c == '1':
            d = self.draft_manager.new_draft(title=self.current_title, content=self.current_content, tags=self.current_tags)
            print(f'Saved: {self.draft_manager.save_current(d)}')
        elif c == '2':
            try:
                d = self.draft_manager.load_draft(drafts[int(input('Index: ').strip())-1]['id'])
                self.current_title = d.content.title; self.current_content = d.content.content
                self.current_tags = d.content.tags; print('Loaded')
            except: print('Invalid')

def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    App().run()

if __name__ == '__main__':
    main()
