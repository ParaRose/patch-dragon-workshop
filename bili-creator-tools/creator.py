"""Bilibili creator-center browser adapter. Run with --help for commands."""
import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parent
UPLOAD = "https://member.bilibili.com/platform/upload/video/frame"
DATA = "https://member.bilibili.com/platform/data-up/video"
COMMENTS = "https://member.bilibili.com/platform/comment"
PROFILE = Path(os.environ["LOCALAPPDATA"]) / "BiliCreatorPilot" / "profile"


def field(page, selector):
    matches = page.locator(selector)
    expect(matches).to_have_count(1, timeout=15000)
    return matches


def submit_video(page, job, video):
    field(page, job.get("file_selector", 'input[type=file][accept*="video"]')).set_input_files(video)
    field(page, job.get("title_selector", 'input[placeholder*="标题"]')).fill(job["title"])
    field(page, job.get("description_selector", '[contenteditable=true][data-placeholder*="简介"]')).fill(job["description"])
    for tag in job["tags"]:
        editor = field(page, job.get("tag_selector", 'input[placeholder*="标签"]'))
        editor.fill(tag)
        editor.press("Enter")
    # Optional category, rights and disclosure controls in the current site layout.
    for selector in job.get("click_before_submit", []):
        field(page, selector).click()
    expect(field(page, job["upload_ready_selector"])).to_be_visible(timeout=900000)
    field(page, job["submit_selector"]).click()
    expect(page.locator(job["receipt_selector"])).to_be_visible(timeout=60000)


def reply(page, job):
    row = field(page, job["comment_selector"])
    expect(row.get_by_text(job["author"], exact=True)).to_be_visible()
    expect(row.get_by_text(job["comment"], exact=True)).to_be_visible()
    if row.get_by_text(job["reply"], exact=True).count():
        raise ValueError("该评论中已出现相同回复，请核对历史记录。")
    row.get_by_text("回复", exact=True).click()
    editor = row.locator(job.get("editor_selector", "textarea"))
    editor.fill(job["reply"])
    row.locator(job["send_selector"]).click()
    expect(row.get_by_text(job["reply"], exact=True)).to_be_visible(timeout=30000)


def snapshot(page, directory, section):
    directory.mkdir(parents=True, exist_ok=True)
    stem = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]
    page.screenshot(path=directory / (stem + ".png"), full_page=True)
    path = directory / (stem + ".json")
    path.write_text(json.dumps({"time": datetime.now().astimezone().isoformat(),
        "url": page.url, "section": section, "text": page.locator("body").inner_text()},
        indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description="B站创作中心运营助手")
    parser.add_argument("action", choices=["login", "upload", "metrics", "comments", "reply"])
    parser.add_argument("--job", type=Path, help="本地 JSON 配置")
    parser.add_argument("--visible", action="store_true")
    args = parser.parse_args()
    job = json.loads(args.job.read_text(encoding="utf-8-sig")) if args.job else {}
    action = args.action
    urls = {"login": UPLOAD, "upload": UPLOAD, "metrics": DATA, "comments": COMMENTS, "reply": COMMENTS}
    url = job.get("url", urls[action])
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "member.bilibili.com":
        parser.error("仅支持 B 站创作中心 HTTPS 页面")
    if action == "upload":
        for key in ("video", "title", "description", "tags", "upload_ready_selector", "submit_selector", "receipt_selector"):
            if key not in job:
                parser.error("缺少字段 " + key)
        video = (args.job.parent / job["video"]).resolve(strict=True)
    with sync_playwright() as engine:
        ctx = engine.chromium.launch_persistent_context(PROFILE, channel="msedge",
            headless=not (args.visible or action == "login"), viewport={"width": 1440, "height": 960})
        try:
            page = ctx.pages[0]
            page.goto(url, wait_until="domcontentloaded")
            if action == "login":
                input("请在独立窗口登录指定 UP 主账号，完成后按回车保存会话。")
                return
            if action == "upload":
                submit_video(page, job, video)
            elif action == "reply":
                reply(page, job)
            else:
                marker = job.get("ready_selector")
                ready = field(page, marker) if marker else page.get_by_text(
                    re.compile("^(播放量|播放数|暂无数据)$" if action == "metrics" else "^(全部评论|暂无评论)$")).first
                expect(ready).to_be_visible(timeout=30000)
            print(snapshot(page, ROOT / "records" / action, action))
        finally:
            ctx.close()


if __name__ == "__main__":
    main()
