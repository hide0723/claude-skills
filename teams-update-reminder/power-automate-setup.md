# Power Automateフロー セットアップガイド

## 前提条件

- Microsoft 365 Business以上のライセンス
- Power Automateへのアクセス権
- Gmailコネクタの承認（初回のみ）

---

## フロー作成手順（画面キャプチャ付き説明）

### 1. 新規フローの作成

1. https://make.powerautomate.com/ にアクセス
2. 左メニュー「**+ 作成**」→「**スケジュール済みクラウドフロー**」
3. 以下を入力して「作成」：
   - フロー名：`Teams更新アプリ 期日超過通知`
   - 開始日時：今日
   - 繰り返し：**1日ごと**、時刻 **08:30**

---

### 2. 変数の初期化

「**+ 新しいステップ**」→「変数を初期化する」を追加（3つ）：

| 変数名 | 種類 | 初期値 |
|--------|------|--------|
| `overdueList` | 文字列 | （空） |
| `overdueCount` | 整数 | 0 |
| `reportDate` | 文字列 | `@{formatDateTime(utcNow(), 'yyyy-MM-dd')}` |

---

### 3. Teams更新リクエストの取得

「**+ 新しいステップ**」→ 検索欄に「**Microsoft Teams**」→「**更新リクエストを一覧表示する**」

> **注意：** コネクタが表示されない場合はStep 3-Bを参照

設定項目：
- チーム：対象チームを選択
- フィルター：`status eq 'notStarted' and dueDateTime le '@{utcNow()}'`

---

### 3-B. Teams更新アプリコネクタがない場合の代替

SharePointリストでUpdateリクエストを管理している場合：

「**SharePoint - 複数の項目の取得**」を使用：
- サイトのアドレス：SharePointサイトのURL
- リスト名：更新リクエスト管理リスト
- フィルタークエリ：`Status eq '未提出' and DueDate le '@{utcNow()}'`

---

### 4. Apply to each（繰り返し処理）

「**+ 新しいステップ**」→「**コントロール**」→「**それぞれに適用する**」

「以前の手順から出力を選択」：`value`（取得したリクエスト一覧）

内部に以下を追加：

#### 4-1. 超過日数の計算

「**変数**」→「**変数に追加する**」でoverdueCountをインクリメント。

「**データ操作**」→「**作成**」で超過日数を計算：
```
@{div(sub(ticks(utcNow()), ticks(items()?['dueDateTime'])), 864000000000)}
```

#### 4-2. overdueListへの追記

「**変数**」→「**文字列変数に追加する**」：
- 名前：`overdueList`
- 値：
```
REQUEST_TITLE: @{items()?['title']}
ASSIGNEE_NAME: @{items()?['responder/displayName']}
ASSIGNEE_EMAIL: @{items()?['responder/email']}
DUE_DATE: @{formatDateTime(items()?['dueDateTime'], 'yyyy-MM-dd')}
OVERDUE_DAYS: @{outputs('作成')}
---
```

---

### 5. 条件分岐（件数チェック）

「**+ 新しいステップ**」→「**コントロール**」→「**条件**」：

- `overdueCount` が `0` より大きい → **はい** の処理へ

---

### 6. Gmailへの通知メール送信（はいの場合）

「**Gmail**」→「**メールの送信**」：

| 項目 | 設定値 |
|------|--------|
| 宛先 | `hide0723@gmail.com` |
| 件名 | `[TEAMS-OVERDUE] 期日超過リスト @{variables('reportDate')}` |
| 本文 | 下記参照 |

**本文：**
```
TEAMS_OVERDUE_REPORT
DATE: @{variables('reportDate')}
COUNT: @{variables('overdueCount')}
---
@{variables('overdueList')}
```

---

### 7. フローのテスト

1. フロー画面右上「**テスト**」→「**手動**」→「**テストの実行**」
2. Gmail受信トレイに `[TEAMS-OVERDUE]` の件名でメールが届くことを確認
3. 本文にリクエスト情報が正しく含まれることを確認

---

## Gmailフィルター設定（推奨）

受信したTEAMS-OVERDUEメールを自動でラベル分類する：

1. Gmail設定 → 「フィルタとブロックしたアドレス」
2. 「新しいフィルタを作成」
3. 件名：`[TEAMS-OVERDUE]`
4. アクション：「ラベルを付ける」→ `teams-overdue` ラベルを作成して適用

これによりClaudeがGmail MCPで確実に検索できる。

---

## よくある問題

### Teams更新アプリのAPIフィールド名が違う

Power AutomateのフローでAPIレスポンスをテストし、実際のフィールド名を確認する：
1. フローテスト実行後、各ステップの「入力/出力」を展開
2. `responder/displayName` や `dueDateTime` の実際のキー名を確認
3. 本文テンプレートのフィールド名を修正

### Gmailコネクタが承認されていない

Power Automate → 「データ」→「接続」→「+ 新しい接続」→「Gmail」で承認する。
