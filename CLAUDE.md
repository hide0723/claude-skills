# CLAUDE.md

このリポジトリで作業する Claude Code セッションへの申し送りです。ここに書かれた
規約・場所は、別のセッションが引き継いでもすぐ使えるように残しています。

## 担当一覧表ジェネレータ（tools/asana_assignment_list.py）

税理士法人 福田会計の Asana プロジェクト「40.税務業務：契約・提案用」
（プロジェクト GID `1204361669585488`）から、SharePoint「30.担当一覧表」の
月次 Excel と同じ書式の HTML ページを組み立てるスクリプト。詳しい使い方・
タブの説明・オプションは `tools/README.md` を参照。設計判断の経緯は
PR #14（`claude/asana-assignment-html-page-xpwd6x` ブランチ）のコミット
メッセージに残っている。

### このリポジトリは公開です — 顧客情報を絶対にコミットしない

関与先名・報酬額・Asana の生の書き出し・スナップショット・生成した HTML は
**一切コミットしない**。`.gitignore` で以下を除外している。

```
担当一覧表*.html
*_担当一覧表.html
asana_tasks*.json
page*.json
snapshots/
R*年*.json
```

コミット前に `git status` で意図しないファイルが混ざっていないか必ず確認する。

### データの置き場所（セッションをまたいで参照するとき）

生成した HTML・Asana からの書き出し JSON・月次スナップショットは、**この
セッションのスクラッチパッドやコンテナには残らない**（セッションごとに
使い捨て）。別の Claude Code セッションが同じデータを参照する必要があるときは:

1. **ユーザーに Asana コネクタを認証してもらい、Asana MCP（`get_tasks`）で
   プロジェクト `1204361669585488` から取り直す**のが基本の経路。
   `opt_fields` は `name,completed,created_at,permalink_url,attachments.name,
   memberships.section.name,custom_fields.name,custom_fields.display_value`
   を指定する（`attachments.name` を落とすと契約書未添付タブが空になる、
   `created_at` を落とすと新規タブが空になる）。1 回のページングで最大 100 件、
   `next_page.offset` を辿って全件取得すること（実測 269 件で 3 ページ）。
2. **月次スナップショット（前月比タブ用）は、ユーザーが SharePoint / OneDrive
   など社内の場所に保管している。** そちらの場所をユーザーに確認してから
   `--snapshot-dir` に渡す。このリポジトリのローカルには存在しない前提で動く。
3. 生成した HTML やスナップショットをユーザーへ渡すときは `SendUserFile` で
   届ける（このセッションのやり方）。Asana の生データそのものを SharePoint へ
   アップロードして永続化する運用は、まだ導入していない — もしユーザーが
   「他のセッションからも同じデータをすぐ読めるようにしたい」と言ったら、
   SharePoint「30.担当一覧表」フォルダに JSON かスナップショットを置く案を
   提案し、置き場所と命名をユーザーと決めてから実装する。

### 変換規則は Python と HTML で二重に持っている

`tools/asana_assignment_list.py` 内の Python 関数 `normalize()` と、生成される
HTML に埋め込む JavaScript 関数 `normalizeTasks()` は同じ変換規則（決算月・
ランク・列の割り振りなど）を持つ。ページ上の「Asanaと同期」ボタンで取り込み
直したときも同じ表になるよう、**片方を直したらもう片方も直す**こと。

### 動作確認の作法

このスクリプトは実データ（顧客情報）でしか実地検証できない。ローカルの
Playwright（`/opt/pw-browsers/chromium`）で HTML を描画し、DOM 計測・
スクリーンショット・PDF 出力で確認してから納品している。添付ファイルの
判定など Asana 側でまだ実データ検証していない機能は、README とコミット
メッセージに「未確認」と明記すること。
