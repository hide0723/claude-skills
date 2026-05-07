---
name: business-plan-teams-update
description: 福田会計の事業計画書PPTをAsanaのタスク進捗と連携しながら毎日更新するスキル。更新完了後はメール送信用にファイルを準備する。「事業計画」「PPT更新」「Asana連携」「進捗更新」などのキーワードが出た場合は必ずこのスキルを使用する。
---

# 事業計画書PPT日次更新スキル

## 概要

2つの処理を自動化する：

1. AsanaのプロジェクトからタスクKPI・進捗を取得
2. 事業計画書PPTの指定スライドを更新して保存

更新完了後はユーザーが手動でメール送信する。

---

## 作業開始前の確認事項

以下をユーザーへ確認する（または会話から特定する）：

- **PPTファイルパス**: 例 `C:\fukuda\business_plan_2026.pptx`
- **更新対象スライド**: 何枚目のスライドを更新するか（不明な場合はStep 2のスライド一覧確認を先に実行）

Asana設定は以下で固定：
- **トークン**: 環境変数 `ASANA_TOKEN`
- **プロジェクトID**: `1211395874851623`（福田会計 事業計画）

---

## 依存ライブラリのインストール（初回のみ）

```bash
pip install python-pptx requests
```

---

## Step 1: Asanaからタスク進捗を取得

```python
import os
import requests

ASANA_TOKEN = os.environ["ASANA_TOKEN"]
PROJECT_ID  = "1211395874851623"

headers = {
    "Authorization": f"Bearer {ASANA_TOKEN}",
    "Accept": "application/json",
}

url = f"https://app.asana.com/api/1.0/projects/{PROJECT_ID}/tasks"
params = {"opt_fields": "name,completed,due_on"}
resp = requests.get(url, headers=headers, params=params)
tasks = resp.json()["data"]

total      = len(tasks)
completed  = sum(1 for t in tasks if t["completed"])
incomplete = total - completed
rate       = round(completed / total * 100, 1) if total > 0 else 0

print(f"タスク合計: {total}  完了: {completed}  未完了: {incomplete}  進捗率: {rate}%")
```

---

## Step 2: PPTのテキスト一覧を確認（初回のみ）

どのスライドのどのテキストボックスを更新するか確認する。

```python
from pptx import Presentation

PPT_PATH = r"C:\fukuda\business_plan_2026.pptx"  # ← 実際のパスに置き換え
prs = Presentation(PPT_PATH)

for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            print(f"スライド{i} | {shape.name} | {shape.text_frame.text[:80]}")
```

出力を確認し、更新すべきテキストボックス名（`shape.name`）を特定する。

---

## Step 3: PPTスライドを更新して保存

```python
from pptx import Presentation
from datetime import date

PPT_PATH = r"C:\fukuda\business_plan_2026.pptx"  # ← 実際のパスに置き換え
prs = Presentation(PPT_PATH)

TARGET_SLIDE_INDEX = 2  # ← 対象スライドのインデックス（0始まり）
slide = prs.slides[TARGET_SLIDE_INDEX]

for shape in slide.shapes:
    if not shape.has_text_frame:
        continue
    text = shape.text_frame.text

    if "進捗率" in text:
        shape.text_frame.paragraphs[0].runs[0].text = \
            f"進捗率：{rate}%（{completed}/{total}件完了）"

    if "更新日" in text:
        shape.text_frame.paragraphs[0].runs[0].text = \
            f"更新日：{date.today().strftime('%Y/%m/%d')}"

prs.save(PPT_PATH)
print(f"✅ PPTを保存しました: {PPT_PATH}")
```

---

## 完了報告

実行後にユーザーへ以下を報告する：

1. Asanaから取得した進捗（完了/合計/進捗率）
2. 更新したスライド番号とテキストボックス名
3. 保存したファイルパス
4. **「メール送信の準備ができました」** と案内する

---

## エラー対応

| エラー | 原因 | 対処 |
|--------|------|------|
| `KeyError: ASANA_TOKEN` | 環境変数未設定 | PowerShellで `SetEnvironmentVariable` を実行後、ターミナルを再起動 |
| `401` (Asana) | トークン期限切れ | Asanaでトークン再発行し環境変数を更新 |
| `IndexError` (PPT) | スライドインデックスが範囲外 | Step 2でスライド一覧を確認して修正 |
| PPTが開けない | 別プロセスで開いている | PowerPointを閉じてから実行 |
