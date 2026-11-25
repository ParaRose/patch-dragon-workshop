# B 站创作中心运营助手

在本目录使用 Python、Playwright 和 Microsoft Edge。首次运行 `python creator.py login`，在独立窗口里登录运营账号并按回车。会话保存在当前 Windows 用户的 LocalAppData 下。

| 命令 | 用途 |
| --- | --- |
| `python creator.py metrics` | 保存创作中心当前显示的流量数据文本和整页截图 |
| `python creator.py comments` | 快照当前评论页 |
| `python creator.py upload --job video.json` | 上传视频，填入标题、简介和标签，提交并等待回执 |
| `python creator.py reply --job reply.json` | 核对指定评论作者和原文，在该条评论下回复 |

首次登录后，根据真实页面确认 URL、分区、原创及 AI 内容声明控件，以及下面的 CSS 选择器。示例中的 ID 仅用于说明格式。所有命令支持 `--visible` 观察页面。读取命令可使用 `--job` 指定当前创作中心页面的 `url` 和加载完成标志 `ready_selector`。数据记录位于 `records`。图表和列表按页面当前筛选范围保存。

投稿任务示例

```json
{
  "video": "首期.mp4",
  "title": "下矿找不到洞口，我给它加了一个路标",
  "description": "Luanti 洞口路标 Mod 实机演示。",
  "tags": ["游戏开发", "Luanti"],
  "click_before_submit": [],
  "upload_ready_selector": "#upload-complete",
  "submit_selector": "#submit-video",
  "receipt_selector": "#submission-receipt"
}
```

回复任务示例

```json
{
  "comment_selector": "[data-comment-id='实际评论ID']",
  "author": "玩家甲",
  "comment": "怎么标记？",
  "reply": "站在洞口输入 /cave mark。",
  "editor_selector": "textarea",
  "send_selector": "button.send"
}
```

如果点击发送或投稿后页面超时，先检查稿件管理或评论记录再决定是否重试。运行 `python -m unittest -v test_creator` 可在本地测试页验证文件选择、填写、提交、回复和快照。
