"""知乎真实发布测试 - 自动检测登录，无需终端输入."""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TITLE = "【测试】多平台发布工具 - 自动化发布测试"
CONTENT = """这是一篇由 Multi-Platform Publisher 自动生成的测试文章。

## 功能验证

本文用于验证以下功能：

1. 浏览器自动化 - Playwright 控制 Chromium 浏览器
2. 自动填写标题 - 自动输入文章标题
3. 自动填写正文 - 自动输入 Markdown 格式内容
4. 自动发布 - 自动点击发布按钮

## 技术栈

- Python 3.13
- Playwright 浏览器自动化
- Markdown 格式支持

本文由自动化工具生成，用于功能测试。"""

os.makedirs("screenshots", exist_ok=True)

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    print("[1/6] Launching browser...")
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    page = context.new_page()

    print("[2/6] Opening zhihu.com...")
    page.goto("https://www.zhihu.com", wait_until="domcontentloaded")
    time.sleep(2)

    # Check login - wait up to 5 minutes
    cookies = context.cookies()
    logged_in = any(c["name"] == "z_c0" for c in cookies)

    if not logged_in:
        print(">>> Please log in to Zhihu in the browser window <<<")
        print(">>> Waiting up to 5 minutes for login... <<<")
        for i in range(150):
            time.sleep(2)
            cookies = context.cookies()
            if any(c["name"] == "z_c0" for c in cookies):
                logged_in = True
                print(f"Login detected after {i*2} seconds!")
                break
            if i % 15 == 0 and i > 0:
                print(f"  Still waiting... ({i*2}s)")

    if not logged_in:
        print("Login timeout. Closing browser.")
        browser.close()
        sys.exit(1)

    print("[3/6] Opening article editor...")
    page.goto("https://zhuanlan.zhihu.com/write", wait_until="domcontentloaded")
    time.sleep(3)
    page.screenshot(path="screenshots/zhihu_1_editor.png")

    print(f"[4/6] Filling title: {TITLE[:30]}...")
    title_el = page.locator('textarea[placeholder]').first
    try:
        title_el.wait_for(timeout=5000)
        title_el.fill(TITLE)
        print("  Title filled.")
    except Exception:
        print("  Trying alternative title selector...")
        page.keyboard.type(TITLE)

    time.sleep(1)

    print("[5/6] Filling content...")
    try:
        editor = page.locator('[contenteditable="true"]').first
        editor.wait_for(timeout=5000)
        editor.click()
        time.sleep(0.3)
        for line in CONTENT.split('\n'):
            if line.strip():
                page.keyboard.type(line, delay=3)
            page.keyboard.press("Enter")
            time.sleep(0.05)
        print("  Content filled.")
    except Exception as e:
        print(f"  Content fill error: {e}")

    time.sleep(2)
    page.screenshot(path="screenshots/zhihu_2_filled.png")
    print("  Screenshot saved: zhihu_2_filled.png")

    print("[6/6] Clicking publish...")
    try:
        btn = page.locator('button:has-text("发布")').first
        btn.wait_for(timeout=5000)
        btn.click()
        time.sleep(2)

        # Confirm dialog
        try:
            confirm = page.locator('button:has-text("确认"), button:has-text("直接发布")').first
            confirm.wait_for(timeout=3000)
            confirm.click()
            time.sleep(3)
        except Exception:
            print("  No confirmation dialog found.")

        page.screenshot(path="screenshots/zhihu_3_published.png")
        print("  Screenshot saved: zhihu_3_published.png")
        print("DONE - Check browser for result!")
    except Exception as e:
        print(f"  Publish button error: {e}")

    # Keep browser open for inspection
    print("Browser will stay open for 60 seconds...")
    time.sleep(60)
    browser.close()

print("Test complete.")
