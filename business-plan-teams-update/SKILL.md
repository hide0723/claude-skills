---
name: business-plan-teams-update
description: 福田会計の事業計画書PPTを、アチーブ質問票の体系（人生理念／重点目標／5つの個別戦略）に沿ってAsanaの進捗と連携しながら毎日更新するスキル。更新後はメール送信用にファイルを準備する。「事業計画」「PPT更新」「Asana連携」「アチーブ」「重点目標」「進捗更新」などのキーワードが出た場合は必ずこのスキルを使用する。
---

# 事業計画書PPT日次更新スキル（アチーブ質問票ベース）

## 概要

福田会計の事業計画は **アチーブ質問票** の体系で構成されている。
本スキルはその体系に沿って、Asanaの進捗を事業計画書PPTへ日次反映する。

1. Asanaプロジェクトからセクション別の進捗を取得
2. アチーブ質問票の区分にマッピング
3. 事業計画書PPTの該当スライドを更新して保存

更新後はユーザーが手動でメール送信する。

---

## アチーブ質問票の体系

### 全体構成

| 区分 | 内容 | データの所在 |
|------|------|------------|
| **Ⅰ．人生理念／ビジョン** | アファメーション（積極宣言8項目）・人生理念 | Notion |
| **Ⅱ．重点目標** | 年度の重点目標 | Notion |
| **Ⅲ．中長期・年間行動計画** | 中長期行動計画表・年間行動計画表 | Notion / Asana |
| **個別戦略（5領域）** | 下表の5戦略 | Asana |

### 個別戦略5領域とAsanaセクションの対応

| アチーブ質問票の区分 | Asanaセクション名 | セクションGID |
|---------------------|------------------|--------------|
| 教育・採用 | 🏫採用・教育・評価 | `1211395874851637` |
| サービス品質 | ✐サービス品質※カテゴリ工事中※ | `1211395874851636` |
| 営業・マーケティング | 📢営業・マーケティング・新商品 | `1211395874851638` |
| 戦略構築・商品開発 | 💡戦略構築※カテゴリ工事中※ | `1210851805791881` |
| 財務体質 | 💰財務・価格政策 | `1211395876829199` |
| （計画作成進捗） | stock:計画作成進捗 | `1210851805791894` |

### 全社戦略の検討項目（プロジェクト概要より）

- PEST分析による外部環境の理解
- 業界の二極化トレンドとポジショニング
- 成長ステージ別の戦略マップ作成
- 2026年に実施すべき10の重要施策の検討
- 表紙・目次の確認と優先テーマの選定
- 船井総研のサポート内容と次のアクション
- 中長期行動計画表の作成
- 年間行動計画表の作成

---

## 接続先情報

| 項目 | 値 |
|------|-----|
| Asanaワークスペース | （税）福田会計/福田公認会計士事務所 |
| Asanaプロジェクト | `02.福田会計　目標設定／計画立案` |
| プロジェクトID | `1211395874851623` |
| トークン | 環境変数 `ASANA_TOKEN` |
| カスタムフィールド「緊急×重要」 | `1212857991183638` |
| カスタムフィールド「検討プラットフォーム」 | `1215232749781366` |

**「緊急×重要」の選択肢：** 1.緊かつ重 / 2.緊 / 3.緊_繰り返し / 4.重 / 5.無

---

## 作業開始前の確認事項

- **PPTファイルパス**: 例 `C:\fukuda\business_plan_2026.pptx`
- **更新対象スライド**: 不明な場合はStep 3のスライド一覧確認を先に実行

---

## 依存ライブラリのインストール（初回のみ）

```bash
pip install python-pptx requests
```

---

## Step 1: Asanaからセクション別の進捗を取得

```python
import os
import requests
from collections import defaultdict

ASANA_TOKEN = os.environ["ASANA_TOKEN"]
PROJECT_ID  = "1211395874851623"   # 02.福田会計 目標設定／計画立案

headers = {
    "Authorization": f"Bearer {ASANA_TOKEN}",
    "Accept": "application/json",
}

# アチーブ質問票の区分 ← Asanaセクション の対応表
SECTION_MAP = {
    "1211395874851637": "教育・採用",
    "1211395874851636": "サービス品質",
    "1211395874851638": "営業・マーケティング",
    "1210851805791881": "戦略構築・商品開発",
    "1211395876829199": "財務体質",
    "1210851805791894": "計画作成進捗",
}

url = f"https://app.asana.com/api/1.0/projects/{PROJECT_ID}/tasks"
params = {"opt_fields": "name,completed,due_on,memberships.section.gid,custom_fields"}
tasks = requests.get(url, headers=headers, params=params).json()["data"]

# セクション別に集計
stats = defaultdict(lambda: {"total": 0, "done": 0})
for t in tasks:
    for m in t.get("memberships", []):
        gid = (m.get("section") or {}).get("gid")
        label = SECTION_MAP.get(gid)
        if label:
            stats[label]["total"] += 1
            if t["completed"]:
                stats[label]["done"] += 1

# 全体集計
total     = len(tasks)
completed = sum(1 for t in tasks if t["completed"])
rate      = round(completed / total * 100, 1) if total else 0

print(f"【全体】{completed}/{total}件 完了（{rate}%）\n")
for label in ["教育・採用", "サービス品質", "営業・マーケティング",
              "戦略構築・商品開発", "財務体質", "計画作成進捗"]:
    s = stats[label]
    r = round(s["done"] / s["total"] * 100, 1) if s["total"] else 0
    print(f"{label}：{s['done']}/{s['total']}件（{r}%）")
```

---

## Step 2: 最優先タスクの抽出（緊急×重要）

事業計画書に「今月の重点アクション」として載せるタスクを抽出する。

```python
URGENT_IMPORTANT_FIELD = "1212857991183638"  # 緊急×重要

priority_tasks = []
for t in tasks:
    if t["completed"]:
        continue
    for cf in t.get("custom_fields", []):
        if cf["gid"] == URGENT_IMPORTANT_FIELD:
            val = (cf.get("enum_value") or {}).get("name", "")
            if val in ("1.緊かつ重", "4.重"):
                priority_tasks.append((val, t["name"], t.get("due_on")))

priority_tasks.sort()
for val, name, due in priority_tasks[:10]:
    print(f"[{val}] {name}（期限: {due or '未設定'}）")
```

---

## Step 3: PPTのテキスト一覧を確認（初回のみ）

どのスライドのどのテキストボックスを更新するか特定する。

```python
from pptx import Presentation

PPT_PATH = r"C:\fukuda\business_plan_2026.pptx"  # ← 実際のパスに置き換え
prs = Presentation(PPT_PATH)

for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            print(f"スライド{i} | {shape.name} | {shape.text_frame.text[:80]}")
```

出力から、5戦略それぞれのスライド番号を控えておく。

---

## Step 4: PPTスライドを更新して保存

アチーブ質問票の区分名をキーに、該当スライドの進捗テキストを書き換える。

```python
from pptx import Presentation
from datetime import date

PPT_PATH = r"C:\fukuda\business_plan_2026.pptx"
prs = Presentation(PPT_PATH)

today_str = date.today().strftime("%Y/%m/%d")

for slide in prs.slides:
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text

        # 各戦略スライドの進捗欄を更新
        for label, s in stats.items():
            if label in text and "進捗" in text:
                r = round(s["done"] / s["total"] * 100, 1) if s["total"] else 0
                shape.text_frame.paragraphs[0].runs[0].text = \
                    f"{label}　進捗：{r}%（{s['done']}/{s['total']}件）"

        # 全体進捗
        if "全体進捗" in text:
            shape.text_frame.paragraphs[0].runs[0].text = \
                f"全体進捗：{rate}%（{completed}/{total}件完了）"

        # 更新日
        if "更新日" in text:
            shape.text_frame.paragraphs[0].runs[0].text = f"更新日：{today_str}"

prs.save(PPT_PATH)
print(f"✅ PPTを保存しました: {PPT_PATH}")
```

---

## Step 5: 完了報告

実行後にユーザーへ以下を報告する：

1. **全体進捗**（完了/合計/進捗率）
2. **5戦略それぞれの進捗**（アチーブ質問票の区分名で表示）
3. **今月の重点アクション**（緊急×重要が「1.緊かつ重」「4.重」の未完了タスク）
4. 更新したスライド番号と保存パス
5. **「メール送信の準備ができました」** と案内する

---

## 補足：Ⅰ・Ⅱ区分（Notion側）の参照

人生理念／ビジョン・重点目標はAsanaではなくNotionに格納されている。

- **データベース**: `01.理念/目標/中長期計画/習慣`
- **Sectionプロパティの値**: Ⅰ．人生理念／ビジョン ／ Ⅱ．重点目標 ／ Ⅲ．中長期・年間行動計画

これらをPPTに反映する場合は、Notion MCPの `notion-search` / `notion-fetch` で該当ページを取得してから転記する。アファメーション（積極宣言8項目）は「Ⅰ．人生理念／ビジョン」配下にある。

---

## エラー対応

| エラー | 原因 | 対処 |
|--------|------|------|
| `KeyError: ASANA_TOKEN` | 環境変数未設定 | PowerShellで設定後、ターミナルを再起動 |
| `401` (Asana) | トークン期限切れ | Asanaでトークン再発行し環境変数を更新 |
| セクション別集計が0件 | `opt_fields` に `memberships.section.gid` が無い | Step 1のparamsを確認 |
| `IndexError` (PPT) | テキストボックスに run が無い（空欄） | `if shape.text_frame.paragraphs[0].runs:` でガードする |
| PPTが開けない | 別プロセスで開いている | PowerPointを閉じてから実行 |
