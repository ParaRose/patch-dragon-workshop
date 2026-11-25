import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from playwright.sync_api import sync_playwright

from creator import reply, snapshot, submit_video


class BrowserFlow(TestCase):
    def test_local_creator_page(self):
        with TemporaryDirectory() as tmp, sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            page.set_content("""<input type=file accept="video/*" onchange="ready.hidden=false">
                <input placeholder="标题"><div contenteditable=true data-placeholder="简介"></div>
                <input placeholder="标签"><p id=ready hidden>上传完成</p>
                <button id=submit onclick="receipt.hidden=false">投稿</button>
                <p id=receipt hidden>投稿成功</p>""")
            video = Path(tmp) / "fixture.mp4"
            video.write_bytes(b"fixture")
            submit_video(page, dict(title="样片", description="预览", tags=["游戏"],
                upload_ready_selector="#ready", submit_selector="#submit", receipt_selector="#receipt"), video)
            self.assertEqual(page.locator('[placeholder="标题"]').input_value(), "样片")
            page.set_content("""<article id=c1><b>玩家甲</b><p>怎么标记？</p>
                <button onclick="box.hidden=false">回复</button><textarea hidden id=box></textarea>
                <button id=send onclick="result.textContent=box.value;box.value=''">发送</button>
                <p id=result></p></article>""")
            job = dict(comment_selector="#c1", author="玩家甲", comment="怎么标记？",
                       reply="输入 /cave mark。", send_selector="#send")
            reply(page, job)
            with self.assertRaises(ValueError):
                reply(page, job)
            page.set_content("<main>播放量 128</main>")
            path = snapshot(page, Path(tmp), "metrics")
            self.assertIn("128", json.loads(path.read_text(encoding="utf-8"))["text"])
            self.assertTrue(path.with_suffix(".png").is_file())
            browser.close()


if __name__ == "__main__":
    main()
