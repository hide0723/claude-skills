---
name: teams-update-reminder
description: Microsoft Teamsの更新アプリで期日を過ぎたタスク・提出物に対してリマインドメッセージを送信するワークフロー。Power Automate連携でTeams更新アプリの未提出情報をGmail経由でClaudeが受け取り、対象者へリマインドメールを自動送信する。「Teamsリマインド」「期日超過」「未提出リマインド」「更新依頼」「督促」などのキーワードが出た場合はこのスキルを使用する。
---

# Teams更新アプリ 期日後リマインドワークフロー

## アーキテクチャ

```
Teams更新アプリ（期日超過検知）
    ↓ Power Automate フロー
Gmail（通知メール受信）← Subject: [TEAMS-OVERDUE] ...
    ↓ Claudeの定期ルーティン（毎朝9時）
Gmail MCPで未提出者リストを読み取り
    ↓
リマインドメール送信（Gmail MCP）
```

---

## Step 1: Power Automateフローの設定

### フロー概要

Teams更新アプリで期日が過ぎた未提出リクエストを検知し、Claudeが読み取れる形式でGmailへ通知メールを送信する。

### フローの作成手順

1. [Power Automate](https://make.powerautomate.com/) にサインイン
2. **「+ 新しいフロー」→「スケジュール済みクラウドフロー」** を選択
3. フロー名：`Teams更新アプリ 期日超過通知`
4. 実行スケジュール：毎日 **08:30**（Claudeルーティン実行の30分前）

### フローのステップ構成

```
[トリガー] スケジュール（毎日08:30）
    ↓
[アクション1] Microsoft Teams - 更新リクエストの一覧を取得
    コネクタ：Microsoft Teams
    アクション：「更新リクエストを一覧表示する」
    フィルター：期日 <= 今日 AND ステータス = 未提出
    ↓
[条件] 未提出リクエストが1件以上あるか？
    ↓ はい
[アクション2] Gmail - メールを送信する
    宛先：hide0723@gmail.com
    件名：[TEAMS-OVERDUE] 期日超過リスト YYYY-MM-DD
    本文：（下記テンプレート参照）
```

### Gmailへの通知メール本文テンプレート

Power Automateの「動的なコンテンツ」を使って以下の形式で本文を作成する：

```
TEAMS_OVERDUE_REPORT
DATE: @{formatDateTime(utcNow(), 'yyyy-MM-dd')}
---
@{join(body('更新リクエストを一覧表示する')?['value'], '
')}
---
FORMAT:
REQUEST_TITLE: @{items()?['title']}
ASSIGNEE_NAME: @{items()?['responder/displayName']}
ASSIGNEE_EMAIL: @{items()?['responder/email']}
DUE_DATE: @{items()?['dueDateTime']}
OVERDUE_DAYS: @{div(sub(ticks(utcNow()), ticks(items()?['dueDateTime'])), 864000000000)}
STATUS: @{items()?['status']}
```

> **補足：** Teams更新アプリのコネクタが利用できない場合は、SharePointリストまたはExcelファイルと連携してデータを取得する方法でも代替可能。

---

## Step 2: Claudeの処理フロー（毎朝9時自動実行）

ルーティンが起動したら以下を実行する：

### 2-1. Gmail通知メールの読み取り

```
Gmail MCPで以下の条件でスレッドを検索：
  - 件名に「[TEAMS-OVERDUE]」を含む
  - 本日受信した未読メール
```

メールが見つからない場合：「本日の期日超過リストは0件です」として終了。

### 2-2. 期日超過リストの解析

メール本文を解析し、以下の情報を抽出する：

| 項目 | 変数名 |
|------|--------|
| リクエストタイトル | REQUEST_TITLE |
| 担当者名 | ASSIGNEE_NAME |
| メールアドレス | ASSIGNEE_EMAIL |
| 期日 | DUE_DATE |
| 超過日数 | OVERDUE_DAYS |

### 2-3. 超過日数に応じたリマインドレベルの判定

| 超過日数 | レベル | 対応 |
|---------|-------|------|
| 1〜2日 | 通常 | 担当者のみへリマインド |
| 3〜5日 | 中度 | 担当者 + 管理者CCでリマインド |
| 6日以上 | 重度 | 担当者へリマインド + 管理者へ別途エスカレーション通知 |

### 2-4. リマインドメールの送信

#### 通常リマインド（1〜2日超過）

```
件名：【リマインド】{REQUEST_TITLE} の提出をお願いします

{ASSIGNEE_NAME} 様

{REQUEST_TITLE} の提出期限（{DUE_DATE}）が {OVERDUE_DAYS} 日超過しています。
お早めにTeamsの更新アプリからご提出ください。

ご不明な点があればご連絡ください。
よろしくお願いいたします。
```

#### 中度リマインド（3〜5日超過）

```
件名：【重要・リマインド】{REQUEST_TITLE} の提出が {OVERDUE_DAYS} 日超過しています

{ASSIGNEE_NAME} 様
CC: {管理者メールアドレス}

{REQUEST_TITLE} の提出期限（{DUE_DATE}）が {OVERDUE_DAYS} 日超過しています。
至急、Teamsの更新アプリからご提出をお願いします。

引き続きご提出いただけない場合、上長へ報告させていただく場合がございます。
```

#### エスカレーション通知（6日以上超過）- 管理者宛

```
件名：【エスカレーション】{ASSIGNEE_NAME} 様より {REQUEST_TITLE} が {OVERDUE_DAYS} 日未提出です

管理者 様

下記の更新リクエストが長期間未提出となっています。ご確認をお願いします。

・リクエスト名：{REQUEST_TITLE}
・担当者：{ASSIGNEE_NAME}（{ASSIGNEE_EMAIL}）
・期日：{DUE_DATE}
・超過日数：{OVERDUE_DAYS} 日

本日、担当者へも督促メールを送信済みです。
```

### 2-5. 完了レポートの出力

全送信完了後、以下を報告する：

```
【リマインド送信完了レポート】
実行日時：YYYY年MM月DD日 09:00
送信件数：X件

[通常リマインド（1〜2日超過）]
・氏名 - リクエスト名（超過Xd）→ 送信済み

[中度リマインド（3〜5日超過）]
・氏名 - リクエスト名（超過Xd）→ 送信済み（管理者CC）

[エスカレーション（6日以上超過）]
・氏名 - リクエスト名（超過Xd）→ 送信済み + 管理者通知済み
```

---

## Step 3: Claudeルーティンの設定

このスキルを起動したとき、ルーティンが未設定であれば以下を案内する：

> 「毎朝9時に自動実行するルーティンを設定しますか？設定する場合、管理者のメールアドレスを教えてください。」

ルーティン設定時のプロンプト例：
```
teams-update-reminderワークフローを実行してください。
管理者メール：{管理者メールアドレス}
リマインド閾値：1日超過から対象
```

---

## Power Automate設定のトラブルシュート

| 問題 | 対処 |
|------|------|
| Teams更新アプリのコネクタがない | SharePoint/ExcelリストでUpdateリクエストを管理する代替構成を使う |
| 動的コンテンツで繰り返し処理できない | 「Apply to each」アクションでループ処理する |
| 件名にフォーマットが入らない | `formatDateTime(utcNow(), 'yyyy-MM-dd')` を式タブで入力する |
| メールが届かない | Power Automateのフロー実行履歴でエラーを確認する |
