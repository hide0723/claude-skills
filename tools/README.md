# tools

事務所業務のちょっとしたスクリプト置き場です。

## asana_assignment_list.py（担当一覧表 HTML ジェネレータ）

Asana プロジェクト「40.税務業務：契約・提案用」のタスクから、SharePoint
「30.担当一覧表」の月次 Excel（`RX年MM月担当一覧表.xlsx`）と同じ書式の
HTML ページを組み立てます。

- **行** … 決算月（1月〜12月／個人／給(有)／給(無)）＝カスタムフィールド「決算月」
- **列** … 担当者＝タスクが属する Asana セクション（＋未割当／CAV）
- **セル** … 関与先名＋ランクバッジ＋他関与者＝「ランク」「他関与者1」
- **件数** … 各決算月行の担当者列の合計（CAV 列と補助業務行「補ー決算／補ー月次」を除く）
- **合計** … 各列に載る全件数

生成されるのは外部リソースを一切読まない単一 HTML です。ランク／担当者での
絞り込み、関与先名の検索、解約・完了済の表示切替、一覧（リスト）形式への
切替がその場で動きます。ライト／ダークどちらのテーマでも読めます。

### 使い方

```bash
# 1. Asana からタスクを書き出す（next_page.offset を辿って全ページ取得する）
curl -H "Authorization: Bearer $ASANA_TOKEN" \
  "https://app.asana.com/api/1.0/tasks?project=1204361669585488&limit=100&opt_fields=\
name,completed,memberships.section.name,custom_fields.name,custom_fields.display_value" \
  > page1.json

# 2. HTML を組み立てる
python3 tools/asana_assignment_list.py page*.json -o 担当一覧表.html --era "令和8年8月度"
```

Claude Code から Asana MCP（`asana_get_tasks`）で取得した JSON もそのまま渡せます。
`--era` を省略すると実行日から和暦を組み立てます。

依存パッケージはありません（Python 3.10 以降の標準ライブラリのみ）。

### 担当者列を変えるとき

`STAFF_COLUMNS` が列の並びです。Asana のセクション名と綴りを合わせてください
（例: `松﨑` は「立つ崎」）。ここに無いセクションのタスクは「未割当」列に入ります。

### 顧客情報の取り扱い

このリポジトリは公開されています。**関与先名・報酬額を含む JSON や、生成した
HTML をコミットしないでください。** 出力先はリポジトリ外を指定してください。
