---
name: evernote-inbox-organization
description: Evernote のインボックスノートブックにあるノートを整理するスキル。ノートのタイトル・本文をもとにクライアント名・資料種別のタグを付け、整理済みノートを指定ノートブック（既定：99.ノート）へ移動する。「Evernote」「エバーノート」「インボックス整理」「ノートタグ付け」「ノートブック移動」などのキーワードが出た場合は必ずこのスキルを使用する。
---

# エバーノートインボックス整理スキル

## 概要

Evernote のインボックスにあるノートを以下の手順で自動整理する：

1. Evernote API 経由でインボックス内のノート一覧を取得
2. ノートのタイトル・本文をもとにクライアント名・資料種別のタグを付与
3. 整理済みノートを「99.ノート」ノートブックへ移動

**実行環境**: Windows PowerShell + Python 3.x

---

## 前提条件の確認

作業開始前にユーザーへ以下を確認する（または会話から特定する）：

- **Evernote Developer Token**: Evernote の開発者トークン（後述の取得手順を参照）
- **インボックスノートブック名**: 既定は `Inbox`（日本語環境では `インボックス`）
- **移動先ノートブック名**: 既定は `99.ノート`
- **タグルール**: クライアント名・資料種別の対応表（ユーザーから提供、または会話で把握済みのものを使用）

---

## Developer Token の取得手順（初回のみ）

Developer Token を持っていない場合、以下の手順で取得する：

1. Evernote にログインした状態でブラウザを開く
2. `https://www.evernote.com/api/DeveloperToken.action` にアクセス
3. 「Create a developer token」をクリック
4. 表示されたトークン文字列をコピーしてユーザーに入力してもらう

> **注意**: Developer Token はアカウント全体へのフルアクセス権を持つ。漏洩しないよう管理すること。

---

## 環境セットアップ（初回のみ）

Python と必要なパッケージをインストールする。

```powershell
# Python がインストール済みか確認
python --version

# evernote3 パッケージをインストール
pip install evernote3
```

---

## Step 1: インボックスのノート一覧取得

以下の Python スクリプトを実行してインボックス内のノートを一覧取得する。

```python
# list_inbox.py
import evernote.api.client as EvernoteClient
from evernote.api.client import EvernoteClient
from evernote.edam.notestore import NoteStore
from evernote.edam.type import ttypes as Types

TOKEN = "YOUR_DEVELOPER_TOKEN"
INBOX_NOTEBOOK_NAME = "Inbox"  # 日本語環境では "インボックス"

client = EvernoteClient(token=TOKEN, sandbox=False)
note_store = client.get_note_store()

# 全ノートブック取得
notebooks = note_store.listNotebooks()
inbox = next((nb for nb in notebooks if nb.name == INBOX_NOTEBOOK_NAME), None)
if inbox is None:
    print(f"ノートブック '{INBOX_NOTEBOOK_NAME}' が見つかりません")
    print("利用可能なノートブック一覧:")
    for nb in notebooks:
        print(f"  - {nb.name}")
    exit(1)

# インボックス内のノートを取得
filter_ = NoteStore.NoteFilter(notebookGuid=inbox.guid)
spec = NoteStore.NotesMetadataResultSpec(
    includeTitle=True,
    includeCreated=True,
    includeTagGuids=True,
)
result = note_store.findNotesMetadata(filter_, 0, 250, spec)

print(f"インボックス内のノート数: {result.totalNotes}")
print()
for i, note in enumerate(result.notes):
    tags = note.tagGuids or []
    print(f"[{i+1}] GUID: {note.guid}")
    print(f"    タイトル: {note.title}")
    print(f"    既存タグ数: {len(tags)}")
    print()
```

```powershell
# PowerShell から実行
python list_inbox.py
```

---

## Step 2: ノート本文の取得（タグ判断用）

タイトルだけでは判断できない場合、ノート本文を取得する。

```python
# get_note_content.py
import sys
import evernote.api.client as EvernoteClient
from evernote.api.client import EvernoteClient
import re

TOKEN = "YOUR_DEVELOPER_TOKEN"
NOTE_GUID = sys.argv[1]  # コマンドライン引数でGUIDを渡す

client = EvernoteClient(token=TOKEN, sandbox=False)
note_store = client.get_note_store()

note = note_store.getNote(NOTE_GUID, True, False, False, False)
# ENMLからプレーンテキストへ変換（タグ除去）
text = re.sub(r'<[^>]+>', '', note.content or "")
text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").strip()

print(f"タイトル: {note.title}")
print(f"本文（先頭500文字）:\n{text[:500]}")
```

```powershell
python get_note_content.py "ノートのGUID"
```

---

## Step 3: タグの判断ルール

ノートのタイトル・本文をもとに以下の2種類のタグを決定する。

### クライアント名タグ

ユーザーから提供された顧客リストとタイトル・本文のキーワードを照合する。
- 顧客リストは会話で把握済みのもの、または以下のように確認する：

```
「タグ付けに使うクライアント名（顧客名）の一覧を教えてください。」
```

### 資料種別タグ

以下の対応表を参考にタイトル・本文から判定する：

| キーワード例 | 資料種別タグ |
|------------|------------|
| 請求書・invoice・請求 | `請求書` |
| 領収書・receipt・レシート | `領収書` |
| 契約書・agreement・contract | `契約書` |
| 議事録・minutes・打合せ | `議事録` |
| 見積書・estimate・見積 | `見積書` |
| 報告書・report | `報告書` |
| 決算・試算表・BS・PL | `決算書類` |
| その他・不明 | `未分類` |

### 判断できない場合

タイトルと本文を提示してユーザーに確認を求める：

```
「以下のノートのタグが判断できません。クライアント名と資料種別を教えてください。
タイトル: [タイトル]
本文: [先頭200文字]」
```

---

## Step 4: タグの付与とノートブック移動

判断したタグを付与し、「99.ノート」ノートブックへ移動する。

```python
# organize_note.py
import sys
import evernote.api.client as EvernoteClient
from evernote.api.client import EvernoteClient
from evernote.edam.type import ttypes as Types

TOKEN = "YOUR_DEVELOPER_TOKEN"
TARGET_NOTEBOOK_NAME = "99.ノート"
NOTE_GUID = sys.argv[1]           # 対象ノートのGUID
NEW_TAGS = sys.argv[2:]           # 付与するタグ名（複数可）

client = EvernoteClient(token=TOKEN, sandbox=False)
note_store = client.get_note_store()

# 移動先ノートブックのGUID取得（なければ作成）
notebooks = note_store.listNotebooks()
target_nb = next((nb for nb in notebooks if nb.name == TARGET_NOTEBOOK_NAME), None)
if target_nb is None:
    new_nb = Types.Notebook(name=TARGET_NOTEBOOK_NAME)
    target_nb = note_store.createNotebook(new_nb)
    print(f"ノートブック '{TARGET_NOTEBOOK_NAME}' を作成しました")

# 既存タグ一覧取得
existing_tags = note_store.listTags()
tag_name_to_guid = {t.name: t.guid for t in existing_tags}

# 必要に応じてタグを作成
tag_guids = []
for tag_name in NEW_TAGS:
    if tag_name in tag_name_to_guid:
        tag_guids.append(tag_name_to_guid[tag_name])
    else:
        new_tag = Types.Tag(name=tag_name)
        created_tag = note_store.createTag(new_tag)
        tag_guids.append(created_tag.guid)
        print(f"タグ '{tag_name}' を新規作成しました")

# ノートを更新（タグ付与 + ノートブック移動）
note = note_store.getNote(NOTE_GUID, False, False, False, False)
note.tagGuids = tag_guids
note.notebookGuid = target_nb.guid
note_store.updateNote(note)

print(f"完了: '{note.title}'")
print(f"  タグ: {', '.join(NEW_TAGS)}")
print(f"  移動先: {TARGET_NOTEBOOK_NAME}")
```

```powershell
# 使用例：GUIDと付与タグを指定して実行
python organize_note.py "abc123-guid" "株式会社〇〇" "請求書"

# タグが3つの場合
python organize_note.py "abc123-guid" "田中税務事務所" "議事録" "2026年度"
```

---

## Step 5: 一括処理フロー

複数ノートをまとめて処理する場合は以下の手順で進める。

1. Step 1 でインボックスのノート一覧を取得
2. 各ノートについて：
   a. タイトルを確認
   b. タイトルで判断できる場合 → タグを決定
   c. タイトルで判断できない場合 → Step 2 で本文を取得してから判断
   d. Step 4 でタグ付け・移動を実行
3. 全ノートの処理が完了したら Step 6 へ

---

## Step 6: 完了報告

処理後にユーザーへ以下を報告する：

1. 処理したノートの総数
2. 付与したタグの一覧と各タグの件数
3. 判断できず保留にしたノート（あれば）
4. 「99.ノート」への移動完了確認

報告例：
```
整理完了: 12件のノートを処理しました。

タグ別件数:
  株式会社〇〇: 4件
  田中税務事務所: 3件
  請求書: 5件
  議事録: 4件
  契約書: 2件
  未分類: 1件

保留（判断不可）: 0件
すべてのノートを「99.ノート」へ移動しました。
```

---

## トラブルシューティング

| エラー | 原因と対処 |
|-------|-----------|
| `EDAMUserException: AUTH_EXPIRED` | Developer Token の期限切れ。再取得すること |
| `ModuleNotFoundError: No module named 'evernote'` | `pip install evernote3` を再実行 |
| ノートブックが見つからない | Step 1 実行時に表示される「利用可能なノートブック一覧」で正確な名称を確認 |
| `EDAMNotFoundException` | GUID が誤っている。Step 1 で再取得すること |
| `RateLimitReachedException` | API レート制限。数分待ってから再実行 |
