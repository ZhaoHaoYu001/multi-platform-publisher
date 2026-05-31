#!/usr/bin/env python3
"""Multi-platform publisher - unified entry point.

Usage:
    python app.py              # Start web panel (default)
    python app.py --web        # Start web panel
    python app.py --cli        # Start interactive CLI
    python app.py --port 8080  # Start web on custom port
"""

import argparse
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_web(host="0.0.0.0", port=5000, debug=False):
    """Start the Flask web panel."""
    from web.app import create_app
    app = create_app()
    print(f"Starting web panel at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


def run_cli():
    """Start the interactive CLI."""
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

    draft_manager = DraftManager()
    media_manager = MediaManager()
    previewer = Previewer()
    rule_engine = RuleEngine(rules_dir=os.path.join(os.path.dirname(__file__), "config", "rules"))
    credential_store = CredentialStore()
    credential_store.load_from_env()
    registry = AdapterRegistry(rule_engine)
    for cls in [WechatAdapter, ZhihuAdapter, BilibiliAdapter, XiaohongshuAdapter, DouyinAdapter, WeiboAdapter]:
        registry.register(cls.platform_name, cls)

    current_title = ""
    current_content = ""
    current_tags: List[str] = []

    def get_adapter(name):
        creds = {p: credential_store.get(p) for p in credential_store.list_platforms()}
        return registry.get(name, credentials=creds.get(name, {}))

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=" * 50)
        print("  Multi-Platform Publisher (CLI)")
        print("=" * 50)
        print(f"Title: {current_title or "(not set)"}")
        print(f"Content: {len(current_content)} chars")
        print(f"Platforms: {", ".join(registry.list_platforms())}")
        print("-" * 50)
        print("1.Edit 2.Media 3.Preview 4.Publish 5.Drafts 0.Exit")
        c = input("Choice: ").strip()

        if c == "1":
            t = input("Title: ").strip()
            if t: current_title = t
            co = input("Content (empty to skip): ").strip()
            if co: current_content = co
            tg = input("Tags (comma): ").strip()
            if tg: current_tags = [x.strip() for x in tg.split(",") if x.strip()]

        elif c == "2":
            p = input("Image path (empty to skip): ").strip()
            if p and os.path.exists(p):
                media_manager.add_image(p)
                print("Added")
            elif p:
                print("Not found")

        elif c == "3":
            if not current_title:
                print("Set title first"); input("Press Enter..."); continue
            images = [i.path for i in media_manager.images]
            try:
                r = previewer.generate_all_previews(title=current_title, content=current_content, images=images, tags=current_tags)
                for p, path in r.items(): print(f"  {p}: {path}")
            except Exception as e: print(f"Error: {e}")
            input("Press Enter...")

        elif c == "4":
            if not current_title:
                print("Set title first"); input("Press Enter..."); continue
            platforms = registry.list_platforms()
            for i, n in enumerate(platforms, 1):
                s = "Y" if credential_store.is_platform_ready(n) else "N"
                print(f"  {i}. {n} [creds:{s}]")
            print(f"  {len(platforms)+1}. All")
            pc = input("Platform: ").strip()
            mc = input("Mode (1=sim 2=real): ").strip()
            mode = PublishMode.REAL if mc == "2" else PublishMode.SIMULATE
            images = [i.path for i in media_manager.images]
            parser = ContentParser()
            doc = parser.parse(current_content, title=current_title, tags=current_tags or None)
            results = {}
            if pc == str(len(platforms)+1):
                for n in platforms:
                    a = get_adapter(n)
                    results[n] = a.publish(doc, images, mode) if a else None
            else:
                try:
                    n = platforms[int(pc)-1]
                    a = get_adapter(n)
                    results[n] = a.publish(doc, images, mode) if a else None
                except: print("Invalid"); input("Press Enter..."); continue
            ok = sum(1 for r in results.values() if r and r.success)
            print(f"Done: {ok}/{len(results)} success")
            for n, r in results.items():
                if r: print(f"  {r}")
            input("Press Enter...")

        elif c == "5":
            drafts = draft_manager.list_drafts()
            for i, d in enumerate(drafts[:5], 1): print(f"  {i}. {d.get("title", "untitled")}")
            print("1.Save 2.Load 0.Back")
            dc = input("Choice: ").strip()
            if dc == "1":
                d = draft_manager.new_draft(title=current_title, content=current_content, tags=current_tags)
                print(f"Saved: {draft_manager.save_current(d)}")
            elif dc == "2":
                try:
                    di = drafts[int(input("Index: ").strip())-1]
                    d = draft_manager.load_draft(di["id"])
                    current_title = d.content.title; current_content = d.content.content
                    current_tags = d.content.tags; print("Loaded")
                except: print("Invalid")

        elif c == "0":
            if current_title or current_content:
                d = draft_manager.new_draft(title=current_title, content=current_content, tags=current_tags)
                draft_manager.save_current(d)
            print("Bye!")
            break


def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    parser = argparse.ArgumentParser(description="Multi-platform publisher")
    parser.add_argument("--web", action="store_true", default=True, help="Start web panel (default)")
    parser.add_argument("--cli", action="store_true", help="Start interactive CLI")
    parser.add_argument("--host", default="0.0.0.0", help="Web host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Web port (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        run_web(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
