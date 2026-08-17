#!/usr/bin/env python3
"""Asana の「40.税務業務：契約・提案用」から担当一覧表（HTML）を組み立てる。

SharePoint の `RX年MM月担当一覧表.xlsx` と同じ書式
（行＝決算月／列＝担当者／セル＝関与先名＋ランク）を HTML で再現する。

使い方:

    # 1. Asana からタスクを書き出す（Asana MCP / REST どちらでも可）
    curl -H "Authorization: Bearer $ASANA_TOKEN" \
      "https://app.asana.com/api/1.0/tasks?project=$PROJECT_GID&limit=100&opt_fields=\
name,completed,memberships.section.name,custom_fields.name,custom_fields.display_value" \
      > page1.json   # next_page.offset を辿って全ページ取得する

    # 2. HTML を組み立てる
    python3 tools/asana_assignment_list.py page*.json -o 担当一覧表.html --era "令和8年8月度"

入力 JSON は Asana API のレスポンス形（``{"data": [...]}``）でも、
タスクの配列そのままでも受け付ける。関与先名などの実データはこのリポジトリには
含めない（顧客情報のため）。生成した HTML はリポジトリ外で保管すること。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

# 担当一覧表の列順（SharePoint の Excel と同じ並び）。Asana のセクション名と対応する。
STAFF_COLUMNS = [
    "純夫",
    "越沼",
    "須藤",
    "荻原",
    "根本",
    "所長",
    "松﨑",
    "南雲",
    "齋籐",
    "英明",
    "高崎：石倉",
]
INBOX_SECTION = "INBOX／担当未割当て"
INBOX_COLUMN = "未割当"
CAV_COLUMN = "CAV"

# 行順。決算月カスタムフィールドの選択肢に対応する。
MONTH_ROWS = [f"{m}月" for m in range(1, 13)] + ["個人", "給(有)", "給(無)"]
UNSET_ROW = "決算月未設定"

# 「件数」に数えないランク（補助業務の追加行）。
SUPPLEMENT_RANKS = {"補ー決算", "補ー月次"}

# タスク名の頭についている整理用の接頭辞。
NAME_PREFIX = re.compile(r"^(?:\[Duplicate\]\s*)?(?:\d{2}|個|給)_\s*")


def load_tasks(paths: Iterable[Path]) -> list[dict[str, Any]]:
    """JSON ファイル群を読み込み、gid で重複を除いたタスク配列を返す。"""
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        page = payload.get("data", payload) if isinstance(payload, dict) else payload
        for task in page:
            gid = task.get("gid") or task.get("name")
            if gid in seen:
                continue
            seen.add(gid)
            tasks.append(task)
    return tasks


def custom_field(task: dict[str, Any], name: str) -> str | None:
    for field in task.get("custom_fields") or []:
        if field.get("name") == name:
            return field.get("display_value")
    return None


def section_of(task: dict[str, Any]) -> str | None:
    for membership in task.get("memberships") or []:
        section = (membership or {}).get("section") or {}
        if section.get("name"):
            return section["name"]
    return None


def normalize(tasks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Asana タスクを一覧表の 1 セル分のレコードに変換する。"""
    records = []
    for task in tasks:
        section = section_of(task)
        column = section
        if section == INBOX_SECTION:
            column = INBOX_COLUMN
        elif section not in STAFF_COLUMNS and section != CAV_COLUMN:
            column = INBOX_COLUMN

        month = custom_field(task, "決算月")
        if month in {str(m) for m in range(1, 13)}:
            row = f"{month}月"
        elif month in {"個人", "給(有)", "給(無)"}:
            row = month
        else:
            row = UNSET_ROW

        records.append(
            {
                "name": NAME_PREFIX.sub("", task.get("name", "")).strip(),
                "row": row,
                "col": column,
                "rank": custom_field(task, "ランク") or "",
                "others": custom_field(task, "他関与者1") or "",
                "done": bool(task.get("completed")),
            }
        )
    records.sort(key=lambda r: (MONTH_ROWS.index(r["row"]) if r["row"] in MONTH_ROWS else 99, r["name"]))
    return records


def build_page(records: list[dict[str, Any]], era: str, generated: str, source: str) -> str:
    columns = STAFF_COLUMNS + [INBOX_COLUMN]
    rows = MONTH_ROWS + ([UNSET_ROW] if any(r["row"] == UNSET_ROW for r in records) else [])
    live = [r for r in records if not r["done"]]
    ranks = Counter(r["rank"] or "―" for r in live if r["col"] != CAV_COLUMN)

    data = {
        "records": records,
        "columns": columns,
        "cavColumn": CAV_COLUMN,
        "rows": rows,
        "supplementRanks": sorted(SUPPLEMENT_RANKS),
    }
    stats = [
        ("関与先件数", len([r for r in live if r["col"] != CAV_COLUMN and r["rank"] not in SUPPLEMENT_RANKS])),
        ("担当者数", len({r["col"] for r in live if r["col"] in STAFF_COLUMNS})),
        ("Aランク", ranks.get("A", 0)),
        ("給与計算", ranks.get("給", 0)),
        ("CAV他関与", len([r for r in live if r["col"] == CAV_COLUMN])),
        ("担当未割当", len([r for r in live if r["col"] == INBOX_COLUMN])),
    ]

    stat_html = "\n".join(
        f'<div class="stat"><span class="stat-label">{html.escape(label)}</span>'
        f'<span class="stat-value">{value}</span></div>'
        for label, value in stats
    )
    rank_chips = "\n".join(
        f'<button type="button" class="chip" data-rank="{html.escape(rank)}" aria-pressed="true">'
        f'<span class="swatch rank-{rank_class(rank)}"></span>{html.escape(rank)}'
        f'<span class="chip-count">{count}</span></button>'
        for rank, count in sorted(ranks.items(), key=lambda kv: rank_order(kv[0]))
    )
    staff_chips = "\n".join(
        f'<button type="button" class="chip" data-col="{html.escape(col)}" aria-pressed="true">{html.escape(col)}</button>'
        for col in columns + [CAV_COLUMN]
    )

    return TEMPLATE.format(
        era=html.escape(era),
        generated=html.escape(generated),
        source=html.escape(source),
        stats=stat_html,
        rank_chips=rank_chips,
        staff_chips=staff_chips,
        data=json.dumps(data, ensure_ascii=False),
    )


def rank_order(rank: str) -> tuple[int, str]:
    order = {"A": 0, "B": 1, "C": 2, "D": 3, "給": 4, "補ー決算": 5, "補ー月次": 6}
    return (order.get(rank, 9), rank)


def rank_class(rank: str) -> str:
    return {"A": "a", "B": "b", "C": "c", "D": "d", "給": "kyu", "補ー決算": "sup", "補ー月次": "sup"}.get(rank, "none")


TEMPLATE = """<title>担当一覧表</title>
<style>
:root {{
  color-scheme: light dark;
  --paper: #f4f6f8;
  --card: #ffffff;
  --card-alt: #f8fafb;
  --ink: #16202b;
  --ink-soft: #4a5765;
  --ink-faint: #7d8b99;
  --rule: #dbe2e9;
  --rule-strong: #b9c5d1;
  --seal: #2b4c7e;
  --seal-soft: #eaf0f8;
  --rank-a: #1b3f6b;
  --rank-b: #35608c;
  --rank-c: #93b0cb;
  --rank-d: #c2cfdb;
  --rank-kyu: #d8ab4a;
  --rank-sup: #b7abd4;
  --badge-ink-strong: #ffffff;
  --badge-ink-pale: #16202b;
  --done: #b04a3f;
  --shadow: 0 1px 2px rgba(22, 32, 43, .06), 0 8px 24px rgba(22, 32, 43, .05);
  --gothic: "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Yu Gothic Medium", "Yu Gothic", "Noto Sans JP", "Meiryo", system-ui, sans-serif;
  --mincho: "Hiragino Mincho ProN", "Yu Mincho", "YuMincho", "Noto Serif JP", "MS PMincho", serif;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", "Roboto Mono", Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --paper: #11161c;
    --card: #171e26;
    --card-alt: #1c242e;
    --ink: #e7edf3;
    --ink-soft: #a9b6c4;
    --ink-faint: #78879a;
    --rule: #2a343f;
    --rule-strong: #3c4956;
    --seal: #8fb4e0;
    --seal-soft: #1e2a3a;
    --rank-a: #a8c8ee;
    --rank-b: #86a9d3;
    --rank-c: #6b8cb3;
    --rank-d: #55708c;
    --rank-kyu: #c99b3f;
    --rank-sup: #9b8bc0;
    --badge-ink-strong: #11161c;
    --badge-ink-pale: #11161c;
    --done: #d97b6d;
    --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 24px rgba(0, 0, 0, .35);
  }}
}}
:root[data-theme="dark"] {{
  --paper: #11161c;
  --card: #171e26;
  --card-alt: #1c242e;
  --ink: #e7edf3;
  --ink-soft: #a9b6c4;
  --ink-faint: #78879a;
  --rule: #2a343f;
  --rule-strong: #3c4956;
  --seal: #8fb4e0;
  --seal-soft: #1e2a3a;
  --rank-a: #a8c8ee;
  --rank-b: #86a9d3;
  --rank-c: #6b8cb3;
  --rank-d: #55708c;
  --rank-kyu: #c99b3f;
  --rank-sup: #9b8bc0;
  --badge-ink-strong: #11161c;
  --badge-ink-pale: #11161c;
  --done: #d97b6d;
  --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 24px rgba(0, 0, 0, .35);
}}

* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--gothic);
  font-size: 15px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}
.wrap {{
  max-width: 1500px;
  margin: 0 auto;
  padding: 32px 20px 72px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}}

/* ── 表題 ─────────────────────────────── */
.masthead {{
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--ink);
}}
.masthead h1 {{
  font-family: var(--mincho);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 600;
  letter-spacing: .22em;
  margin: 0;
  text-wrap: balance;
}}
.masthead .org {{
  display: block;
  font-family: var(--gothic);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .18em;
  color: var(--ink-faint);
  margin-bottom: 6px;
}}
.meta {{
  font-size: 12px;
  color: var(--ink-soft);
  text-align: right;
  line-height: 1.9;
}}
.meta b {{ font-family: var(--mincho); font-size: 15px; font-weight: 600; color: var(--ink); letter-spacing: .1em; }}
.meta code {{ font-family: var(--mono); font-size: 11px; color: var(--ink-faint); }}

/* ── 集計 ─────────────────────────────── */
.stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 1px;
  background: var(--rule);
  border: 1px solid var(--rule);
  border-radius: 3px;
  overflow: hidden;
}}
.stat {{
  background: var(--card);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}}
.stat-label {{ font-size: 11px; letter-spacing: .14em; color: var(--ink-faint); }}
.stat-value {{
  font-family: var(--mono);
  font-variant-numeric: tabular-nums;
  font-size: 26px;
  line-height: 1.15;
  font-weight: 600;
}}

/* ── 操作 ─────────────────────────────── */
.controls {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 18px;
  padding: 14px 16px;
  background: var(--card);
  border: 1px solid var(--rule);
  border-radius: 3px;
  box-shadow: var(--shadow);
}}
.control-group {{ display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }}
.control-group > .legend {{
  font-size: 11px;
  letter-spacing: .14em;
  color: var(--ink-faint);
  margin-right: 2px;
}}
.chip {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font: inherit;
  font-size: 12.5px;
  padding: 4px 10px;
  border: 1px solid var(--rule-strong);
  border-radius: 999px;
  background: var(--card);
  color: var(--ink-soft);
  cursor: pointer;
  transition: background .12s, color .12s, border-color .12s;
}}
.chip:hover {{ border-color: var(--seal); }}
.chip[aria-pressed="true"] {{ background: var(--seal-soft); border-color: var(--seal); color: var(--ink); }}
.chip[aria-pressed="false"] {{ opacity: .45; text-decoration: line-through; }}
.chip-count {{ font-family: var(--mono); font-variant-numeric: tabular-nums; font-size: 11px; color: var(--ink-faint); }}
.swatch {{ width: 9px; height: 9px; border-radius: 2px; display: inline-block; }}
.rank-a {{ background: var(--rank-a); }}
.rank-b {{ background: var(--rank-b); }}
.rank-c {{ background: var(--rank-c); }}
.rank-d {{ background: var(--rank-d); }}
.rank-kyu {{ background: var(--rank-kyu); }}
.rank-sup {{ background: var(--rank-sup); }}
.rank-none {{ background: var(--rule-strong); }}

.search {{
  flex: 1 1 200px;
  min-width: 180px;
  font: inherit;
  font-size: 13px;
  padding: 6px 10px;
  border: 1px solid var(--rule-strong);
  border-radius: 3px;
  background: var(--card);
  color: var(--ink);
}}
.search::placeholder {{ color: var(--ink-faint); }}
.toggle {{ display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--ink-soft); cursor: pointer; }}
.toggle input {{ accent-color: var(--seal); }}
:where(button, input, a):focus-visible {{ outline: 2px solid var(--seal); outline-offset: 2px; }}

/* ── 表 ───────────────────────────────── */
.sheet {{
  background: var(--card);
  border: 1px solid var(--rule-strong);
  border-radius: 3px;
  box-shadow: var(--shadow);
  overflow: auto;
  max-height: 78vh;
}}
table {{ border-collapse: separate; border-spacing: 0; width: max-content; min-width: 100%; font-size: 13px; }}
th, td {{
  border-right: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
  padding: 4px 8px;
  text-align: left;
  vertical-align: top;
  white-space: nowrap;
}}
tbody td {{ min-width: 6.5em; }}
thead th {{
  position: sticky;
  top: 0;
  z-index: 3;
  background: var(--card-alt);
  border-bottom: 2px solid var(--ink);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .1em;
  white-space: nowrap;
  color: var(--ink);
}}
th.rowhead, thead th.corner {{
  position: sticky;
  left: 0;
  background: var(--card-alt);
  z-index: 2;
  border-right: 2px solid var(--rule-strong);
  font-family: var(--mincho);
  font-size: 14px;
  letter-spacing: .1em;
  white-space: nowrap;
  text-align: center;
  vertical-align: middle;
  min-width: 84px;
}}
thead th.corner {{ z-index: 4; }}
th.col-count, td.col-count {{ text-align: right; background: var(--card-alt); }}
th.col-cav, td.col-cav {{ border-left: 2px solid var(--rule-strong); }}
tbody tr:nth-child(even) td:not(.col-count) {{ background: color-mix(in srgb, var(--card-alt) 55%, transparent); }}
tbody tr.total th, tbody tr.total td {{
  border-top: 2px solid var(--ink);
  background: var(--card-alt);
  font-weight: 600;
}}
tbody tr.total td {{ text-align: right; }}
.count {{ font-family: var(--mono); font-variant-numeric: tabular-nums; }}
.count.zero {{ color: var(--ink-faint); font-weight: 400; }}

/* ── セル ─────────────────────────────── */
.entry {{
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 2px 6px;
  padding: 1px 0;
  line-height: 1.45;
  max-width: 17em;
  white-space: normal;
  overflow-wrap: anywhere;
}}
.entry + .entry {{ border-top: 1px dotted var(--rule); }}
.entry .nm {{ flex: 0 1 auto; min-width: 0; }}
.entry.is-done .nm {{ color: var(--done); text-decoration: line-through; text-decoration-thickness: 1px; }}
.entry.is-dim {{ opacity: .22; }}
.entry.is-hit .nm {{ background: color-mix(in srgb, var(--seal) 18%, transparent); border-radius: 2px; }}
.badge {{
  flex: none;
  font-family: var(--mono);
  font-size: 10px;
  line-height: 1.5;
  padding: 0 4px;
  border-radius: 2px;
  color: var(--badge-ink-strong);
  letter-spacing: .04em;
}}
.badge.rank-c, .badge.rank-d, .badge.rank-kyu, .badge.rank-sup, .badge.rank-none {{ color: var(--badge-ink-pale); }}
.badge.rank-a {{ background: var(--rank-a); }}
.badge.rank-b {{ background: var(--rank-b); }}
.badge.rank-c {{ background: var(--rank-c); }}
.badge.rank-d {{ background: var(--rank-d); }}
.badge.rank-kyu {{ background: var(--rank-kyu); }}
.badge.rank-sup {{ background: var(--rank-sup); }}
.badge.rank-none {{ background: var(--rule-strong); }}
.others {{ flex: none; font-size: 10.5px; color: var(--ink-faint); }}

/* ── 一覧（リスト）表示 ────────────────── */
.list-view {{ display: none; }}
body.mode-list .sheet.matrix {{ display: none; }}
body.mode-list .list-view {{ display: block; }}
.list-view table {{ font-size: 13px; }}
.list-view td.nm {{ min-width: 240px; }}
.list-view th {{ cursor: default; }}

footer {{
  font-size: 11.5px;
  color: var(--ink-faint);
  line-height: 1.9;
  border-top: 1px solid var(--rule);
  padding-top: 14px;
}}
footer b {{ color: var(--ink-soft); }}
@media (max-width: 720px) {{
  .wrap {{ padding: 20px 12px 48px; }}
  .meta {{ text-align: left; }}
  .sheet {{ max-height: 70vh; }}
}}
</style>

<div class="wrap">
  <header class="masthead">
    <h1><span class="org">税理士法人 福田会計</span>担当一覧表</h1>
    <div class="meta">
      <b>{era}</b><br>
      出力日 {generated}<br>
      <code>{source}</code>
    </div>
  </header>

  <section class="stats" aria-label="集計">
{stats}
  </section>

  <section class="controls" aria-label="絞り込み">
    <div class="control-group">
      <span class="legend">ランク</span>
{rank_chips}
    </div>
    <div class="control-group">
      <span class="legend">担当</span>
{staff_chips}
    </div>
    <input class="search" type="search" id="q" placeholder="関与先名で検索" aria-label="関与先名で検索">
    <label class="toggle"><input type="checkbox" id="showDone"> 解約・完了済を表示</label>
    <label class="toggle"><input type="checkbox" id="listMode"> 一覧形式</label>
  </section>

  <div class="sheet matrix">
    <table id="matrix">
      <thead><tr id="matrix-head"></tr></thead>
      <tbody id="matrix-body"></tbody>
    </table>
  </div>

  <div class="sheet list-view">
    <table id="list">
      <thead><tr><th>決算月</th><th>関与先名</th><th>担当</th><th>ランク</th><th>他関与者</th></tr></thead>
      <tbody id="list-body"></tbody>
    </table>
  </div>

  <footer>
    <b>件数</b>＝各決算月行の担当者列の合計（CAV列・補助業務行「補ー決算／補ー月次」を除く）。
    <b>合計</b>＝各列に載る全件数。<br>
    出典は Asana プロジェクト「40.税務業務：契約・提案用」のタスクと、カスタムフィールド「決算月」「ランク」「他関与者1」。
    列はタスクが属するセクション（担当者）。書式は SharePoint「30.担当一覧表」の月次 Excel に合わせています。
  </footer>
</div>

<script>
const DATA = {data};

const RANK_CLASS = {{"A":"a","B":"b","C":"c","D":"d","給":"kyu","補ー決算":"sup","補ー月次":"sup"}};
const rankClass = r => "rank-" + (RANK_CLASS[r] || "none");
const SUPPLEMENT = new Set(DATA.supplementRanks);
const ALL_COLUMNS = DATA.columns.concat([DATA.cavColumn]);

const state = {{
  ranks: new Set(DATA.records.map(r => r.rank || "―")),
  cols: new Set(ALL_COLUMNS),
  query: "",
  showDone: false,
}};

const esc = s => String(s).replace(/[&<>"]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}})[c]);

function visibleColumns() {{
  return DATA.columns.filter(c => state.cols.has(c));
}}

function activeRecords() {{
  return DATA.records.filter(r =>
    (state.showDone || !r.done) &&
    state.ranks.has(r.rank || "―") &&
    state.cols.has(r.col)
  );
}}

function entryHTML(rec) {{
  const hit = state.query && rec.name.toLowerCase().includes(state.query);
  const dim = state.query && !hit;
  const cls = ["entry", rec.done ? "is-done" : "", hit ? "is-hit" : "", dim ? "is-dim" : ""].filter(Boolean).join(" ");
  const others = rec.others ? `<span class="others">＋${{esc(rec.others)}}</span>` : "";
  const badge = rec.rank ? `<span class="badge ${{rankClass(rec.rank)}}">${{esc(rec.rank)}}</span>` : "";
  return `<div class="${{cls}}"><span class="nm">${{esc(rec.name)}}</span>${{badge}}${{others}}</div>`;
}}

function renderMatrix() {{
  const cols = visibleColumns();
  const showCav = state.cols.has(DATA.cavColumn);
  const recs = activeRecords();

  const head = ['<th class="corner">決算月</th>']
    .concat(cols.map(c => `<th>${{esc(c)}}</th>`))
    .concat(['<th class="col-count">件数</th>'])
    .concat(showCav ? [`<th class="col-cav">${{esc(DATA.cavColumn)}}</th>`] : []);
  document.getElementById("matrix-head").innerHTML = head.join("");

  const totals = {{}};
  ALL_COLUMNS.forEach(c => totals[c] = 0);
  let grand = 0;

  const body = DATA.rows.map(row => {{
    const inRow = recs.filter(r => r.row === row);
    if (!inRow.length && !DATA.rows.slice(0, 12).includes(row)) return "";
    let count = 0;
    const cells = cols.map(col => {{
      const list = inRow.filter(r => r.col === col);
      totals[col] += list.length;
      count += list.filter(r => !SUPPLEMENT.has(r.rank)).length;
      return `<td>${{list.map(entryHTML).join("")}}</td>`;
    }});
    grand += count;
    const cav = inRow.filter(r => r.col === DATA.cavColumn);
    totals[DATA.cavColumn] += cav.length;
    const cavCell = showCav ? `<td class="col-cav">${{cav.map(entryHTML).join("")}}</td>` : "";
    return `<tr><th class="rowhead">${{esc(row)}}</th>${{cells.join("")}}` +
      `<td class="col-count"><span class="count${{count ? "" : " zero"}}">${{count}}</span></td>${{cavCell}}</tr>`;
  }}).join("");

  const totalRow = `<tr class="total"><th class="rowhead">合計</th>` +
    cols.map(c => `<td><span class="count">${{totals[c]}}</span></td>`).join("") +
    `<td class="col-count"><span class="count">${{grand}}</span></td>` +
    (showCav ? `<td class="col-cav"><span class="count">${{totals[DATA.cavColumn]}}</span></td>` : "") +
    `</tr>`;

  document.getElementById("matrix-body").innerHTML = body + totalRow;
}}

function renderList() {{
  const recs = activeRecords()
    .filter(r => !state.query || r.name.toLowerCase().includes(state.query));
  document.getElementById("list-body").innerHTML = recs.map(r =>
    `<tr><th class="rowhead">${{esc(r.row)}}</th>` +
    `<td class="nm${{r.done ? " is-done" : ""}}">${{esc(r.name)}}</td>` +
    `<td>${{esc(r.col)}}</td>` +
    `<td>${{r.rank ? `<span class="badge ${{rankClass(r.rank)}}">${{esc(r.rank)}}</span>` : ""}}</td>` +
    `<td><span class="others">${{esc(r.others)}}</span></td></tr>`
  ).join("");
}}

function render() {{ renderMatrix(); renderList(); }}

document.querySelectorAll(".chip[data-rank]").forEach(chip => {{
  chip.addEventListener("click", () => {{
    const rank = chip.dataset.rank;
    const on = chip.getAttribute("aria-pressed") === "true";
    chip.setAttribute("aria-pressed", String(!on));
    on ? state.ranks.delete(rank) : state.ranks.add(rank);
    render();
  }});
}});
document.querySelectorAll(".chip[data-col]").forEach(chip => {{
  chip.addEventListener("click", () => {{
    const col = chip.dataset.col;
    const on = chip.getAttribute("aria-pressed") === "true";
    chip.setAttribute("aria-pressed", String(!on));
    on ? state.cols.delete(col) : state.cols.add(col);
    render();
  }});
}});
document.getElementById("q").addEventListener("input", e => {{
  state.query = e.target.value.trim().toLowerCase();
  render();
}});
document.getElementById("showDone").addEventListener("change", e => {{
  state.showDone = e.target.checked;
  render();
}});
document.getElementById("listMode").addEventListener("change", e => {{
  document.body.classList.toggle("mode-list", e.target.checked);
}});

render();
</script>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Asana のタスクから担当一覧表 HTML を生成する")
    parser.add_argument("inputs", nargs="+", type=Path, help="Asana タスクの JSON ファイル")
    parser.add_argument("-o", "--output", type=Path, default=Path("担当一覧表.html"))
    parser.add_argument("--era", default="", help='表題横の年月（例: "令和8年8月度"）')
    parser.add_argument("--source", default="Asana / 40.税務業務：契約・提案用", help="出典の表示文字列")
    args = parser.parse_args(argv)

    tasks = load_tasks(args.inputs)
    if not tasks:
        print("タスクが読み込めませんでした", file=sys.stderr)
        return 1

    records = normalize(tasks)
    today = dt.date.today()
    era = args.era or f"令和{today.year - 2018}年{today.month}月度"
    page = build_page(records, era, today.strftime("%Y/%m/%d"), args.source)
    args.output.write_text(page, encoding="utf-8")
    print(f"{args.output} を書き出しました（{len(records)} 件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
