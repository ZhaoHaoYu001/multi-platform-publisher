#!/usr/bin/env python3
import argparse, os, sys
from typing import Dict, List
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
from src.core.platform_base import PublishMode, PublishResult
from src.core.rule_engine import RuleEngine

def load_content(content, content_file):
    if content_file:
        if not os.path.exists(content_file):
            print(f'Error: file not found - {content_file}'); sys.exit(1)
        with open(content_file, 'r', encoding='utf-8') as f: return f.read()
    return content

def load_images(image_paths):
    return [p for p in image_paths if os.path.exists(p)]

def init_registry(platforms):
    from dotenv import load_dotenv
    load_dotenv()
    engine = RuleEngine(rules_dir=os.path.join(os.path.dirname(__file__), 'config', 'rules'))
    registry = AdapterRegistry(engine)
    avail = {'wechat': WechatAdapter, 'zhihu': ZhihuAdapter, 'bilibili': BilibiliAdapter,
             'xiaohongshu': XiaohongshuAdapter, 'douyin': DouyinAdapter, 'weibo': WeiboAdapter}
    for name in platforms:
        if name in avail: registry.register(name, avail[name])
        else: print(f'Warning: unknown platform - {name}')
    return registry

def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    parser = argparse.ArgumentParser(description='Multi-platform publisher')
    parser.add_argument('-t', '--title', required=True)
    parser.add_argument('-c', '--content', default='')
    parser.add_argument('-f', '--content-file')
    parser.add_argument('--tags', default='')
    parser.add_argument('-p', '--platforms', default='wechat,zhihu,bilibili,xiaohongshu,douyin,weibo')
    parser.add_argument('-i', '--images', nargs='*', default=[])
    mg = parser.add_mutually_exclusive_group()
    mg.add_argument('--simulate', action='store_true', default=True)
    mg.add_argument('--real', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    content = load_content(args.content, args.content_file)
    if not content: print('Error: empty content'); sys.exit(1)

    images = load_images(args.images)
    platforms = [p.strip() for p in args.platforms.split(',') if p.strip()]
    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    mode = PublishMode.REAL if args.real else PublishMode.SIMULATE

    registry = init_registry(platforms)
    if not registry.list_platforms(): print('Error: no platforms'); sys.exit(1)

    cs = CredentialStore(); cs.load_from_env()
    parser2 = ContentParser()
    doc = parser2.parse(content, title=args.title, tags=tags or None)

    print('=' * 50)
    print('Multi-Platform Publisher')
    print('=' * 50)
    print(f'Title: {args.title}')
    print(f'Content: {len(content)} chars')
    print(f'Platforms: {", ".join(registry.list_platforms())}')
    print(f'Mode: {"real" if mode == PublishMode.REAL else "simulate"}')
    print('-' * 50)
    print()

    results: Dict[str, PublishResult] = {}
    for pn in registry.list_platforms():
        creds = cs.get(pn)
        adapter = registry.get(pn, credentials=creds)
        if adapter is None:
            results[pn] = PublishResult(success=False, platform=pn, message='not registered')
        else:
            results[pn] = adapter.publish(doc, images, mode)

    ok = sum(1 for r in results.values() if r.success)
    print(f'Done: {ok}/{len(results)} success')
    for n, r in results.items(): print(f'  {r}')

    if args.verbose:
        for n, r in results.items():
            print(f'[{n}] success={r.success} msg={r.message}')
            if r.url: print(f'  url={r.url}')

    if ok == 0 and mode == PublishMode.REAL: sys.exit(1)

if __name__ == '__main__': main()
