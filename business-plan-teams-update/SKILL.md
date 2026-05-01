---
name: business-plan-teams-update
description: 福田会計の事業計画書PPTをAsanaのタスク進捗と連携しながら毎日更新し、毎月1日にMicrosoft TeamsチャネルへサマリーをIncoming Webhookで投稿するスキル。「事業計画」「Teams投稿」「Asana連携」「PPT更新」「月次報告」などのキーワードが出た場合は必ずこのスキルを使用する。
---

# 事業計画書PPT更新・Teams月次投稿スキル

## 概要

3つの処理を自動化する：

1. AsanaのプロジェクトからタスクKPI・進捗を取得
2. 事業計画書PPTの指定スライドを毎日更新
3. 毎月1日にTeams Incoming WebhookへサマリーをPOST

---

## 作業開始前の確認事項

以下をユーザーへ確認する（または会話から特定する）：

- **PPTファイルパス**: 例 `C:\fukuda\business_plan_2026.pptx`
- **Asanaパーソナルアクセストークン**: 環境変数 `ASANA_TOKEN` に設定済み
- **AsanaプロジェクトID**: `1211395874851623`（福田会計 事業計画）
- **Teams Incoming Webhook URL**: Teamsチャネル → コネクタ → 受信Webhook → 構成
- **作業種別**: 「日次更新のみ」「Teams投稿のみ」「両方」

---

## 依存ライブラリのインストール

```bash
pip install python-pptx requests
```

---

## Step 1: Asanaからタスク進捗を取得

```python
import requests

ASANA_TOKEN = os.environ["ASANA_TOKEN"]  # 環境変数から取得
PROJECT_ID  = "1211395874851623"         # 福田会計 事業計画プロジェクト

headers = {
    "Authorization": f"Bearer {ASANA_TOKEN}",
    "Accept": "application/json",
}

# プロジェクト内の全タスクを取得
url = f"https://app.asana.com/api/1.0/projects/{PROJECT_ID}/tasks"
params = {"opt_fields": "name,completed,due_on,assignee.name,custom_fields"}
resp = requests.get(url, headers=headers, params=params)
tasks = resp.json()["data"]

total     = len(tasks)
completed = sum(1 for t in tasks if t["completed"])
incomplete = total - completed
rate      = round(completed / total * 100, 1) if total > 0 else 0

print(f"タスク合計: {total}  完了: {completed}  未完了: {incomplete}  進捗率: {rate}%")
```

---

## Step 2: PPTのスライドを更新（python-pptx）

PPTの特定テキストボックスを進捗データで上書きする。

```python
from pptx import Presentation
from pptx.util import Pt
from datetime import date

PPT_PATH = r"C:\fukuda\business_plan_2026.pptx"  # ← 実際のパスに置き換え

prs = Presentation(PPT_PATH)

# 更新対象スライドのインデックス（0始まり）
TARGET_SLIDE_INDEX = 2  # 例: 3枚目のスライドを更新

slide = prs.slides[TARGET_SLIDE_INDEX]

# テキストボックスのプレースホルダー名で特定して書き換え
for shape in slide.shapes:
    if not shape.has_text_frame:
        continue

    # 「進捗率」と書かれたテキストボックスを更新
    if "進捗率" in shape.text_frame.text:
        tf = shape.text_frame
        tf.paragraphs[0].runs[0].text = f"進捗率：{rate}%（{completed}/{total}件完了）"

    # 「更新日」と書かれたテキストボックスを更新
    if "更新日" in shape.text_frame.text:
        tf = shape.text_frame
        tf.paragraphs[0].runs[0].text = f"更新日：{date.today().strftime('%Y/%m/%d')}"

prs.save(PPT_PATH)
print(f"PPTを保存しました: {PPT_PATH}")
```

> **スライドのどこを更新するか分からない場合は以下でテキスト一覧を確認する：**
>
> ```python
> for i, slide in enumerate(prs.slides):
>     for shape in slide.shapes:
>         if shape.has_text_frame:
>             print(f"スライド{i} | {shape.name} | {shape.text_frame.text[:60]}")
> ```

---

## Step 3: 毎月1日のTeams投稿

```python
import json
from datetime import date

WEBHOOK_URL = "YOUR_TEAMS_WEBHOOK_URL"  # ← 実際のURLに置き換え

today = date.today()

# 月初チェック（強制投稿する場合は条件を削除）
if today.day != 1:
    print(f"本日({today})は月初ではないためTeams投稿をスキップします")
else:
    prev_month = today.month - 1 if today.month > 1 else 12
    prev_year  = today.year if today.month > 1 else today.year - 1

    payload = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": f"📊 福田会計 {prev_year}年{prev_month}月 事業計画レポート",
                        "size": "Large",
                        "weight": "Bolder",
                        "color": "Accent"
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {"title": "タスク進捗率", "value": f"{rate}%"},
                            {"title": "完了タスク",   "value": f"{completed} / {total} 件"},
                            {"title": "未完了タスク", "value": f"{incomplete} 件"},
                            {"title": "更新日",       "value": today.strftime("%Y/%m/%d")},
                        ]
                    }
                ]
            }
        }]
    }

    resp = requests.post(
        WEBHOOK_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    print(f"Teams投稿完了: HTTP {resp.status_code}")
```

---

## 日次自動実行の設定

### Windowsタスクスケジューラ（管理者PowerShellで実行）

```powershell
$action  = New-ScheduledTaskAction -Execute "python.exe" `
           -Argument "C:\fukuda\update_business_plan.py"
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
Register-ScheduledTask -TaskName "福田会計_事業計画更新" `
    -Action $action -Trigger $trigger -RunLevel Highest
```

---

## 認証情報の管理

トークンやWebhook URLは環境変数で管理し、スクリプトにハードコードしない。

```powershell
# PowerShellで環境変数を設定（永続化）
[System.Environment]::SetEnvironmentVariable("ASANA_TOKEN",   "xxxx", "User")
[System.Environment]::SetEnvironmentVariable("TEAMS_WEBHOOK", "https://...", "User")
```

```python
# Pythonスクリプト側で読み込む
import os
ASANA_TOKEN = os.environ["ASANA_TOKEN"]
WEBHOOK_URL = os.environ["TEAMS_WEBHOOK"]
```

---

## エラー対応

| エラー | 原因 | 対処 |
|--------|------|------|
| `401` (Asana) | トークン期限切れ | Asanaでトークン再発行 |
| `KeyError: 'data'` | プロジェクトIDが間違い | URLのID部分を再確認 |
| `IndexError` (PPT) | スライドインデックスが範囲外 | `TARGET_SLIDE_INDEX` を確認 |
| Teams `400` | Adaptive CardのJSONが不正 | `json.dumps` 出力を確認 |
| PPTが開けない | 別プロセスで開いている | PowerPointを閉じてから実行 |

---

## 完了報告

実行後にユーザーへ以下を報告する：

1. Asanaから取得したタスク進捗（完了/合計/進捗率）
2. PPT更新の完了確認（更新したスライド番号）
3. Teams投稿の実施有無と結果
4. 次回実行予定日
