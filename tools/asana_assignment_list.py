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

できあがった HTML はページ上の「Asanaと同期」ボタンから自分で Asana を叩いて
最新化できる（個人用アクセストークンが要る）。つながらない環境では、同じ
ダイアログから書き出し済みの JSON を読み込める。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

PROJECT_GID = "1204361669585488"

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
BASE_ROWS = [f"{m}月" for m in range(1, 13)] + ["個人", "給(有)", "給(無)"]
UNSET_ROW = "決算月未設定"

# 「件数」に数えないランク（補助業務の追加行）。
SUPPLEMENT_RANKS = ["補ー決算", "補ー月次"]

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


def task_url(task: dict[str, Any]) -> str:
    """タスクを開く URL。opt_fields に permalink_url が無くても gid から組める。"""
    if task.get("permalink_url"):
        return task["permalink_url"]
    gid = task.get("gid")
    return f"https://app.asana.com/0/{PROJECT_GID}/{gid}" if gid else ""


def normalize(tasks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Asana タスクを一覧表の 1 セル分のレコードに変換する。

    ここでの変換規則は HTML 側の normalizeTasks() と揃えてある。同期ボタンで
    取り込み直したときに同じ表になるよう、片方を直したらもう片方も直すこと。
    """
    records = []
    for task in tasks:
        section = section_of(task)
        column = section if section in STAFF_COLUMNS or section == CAV_COLUMN else INBOX_COLUMN

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
                # Asana にタスクが登録された日。契約開始日そのものではないが、
                # 新規関与先を年度で拾うにはこれが一番近い。
                "created": (task.get("created_at") or "")[:10],
                "channel": custom_field(task, "契約・紹介チャネル") or "",
                "url": task_url(task),
            }
        )
    records.sort(key=lambda r: (BASE_ROWS.index(r["row"]) if r["row"] in BASE_ROWS else 99, r["name"]))
    return records


def build_page(records: list[dict[str, Any]], era: str, synced: str, source: str) -> str:
    data = {
        "records": records,
        "columns": STAFF_COLUMNS + [INBOX_COLUMN],
        "inboxColumn": INBOX_COLUMN,
        "cavColumn": CAV_COLUMN,
        "inboxSection": INBOX_SECTION,
        "baseRows": BASE_ROWS,
        "unsetRow": UNSET_ROW,
        "supplementRanks": SUPPLEMENT_RANKS,
        "projectGid": PROJECT_GID,
        "synced": synced,
    }
    page = TEMPLATE
    for token, value in {
        "__ERA__": html.escape(era),
        "__SOURCE__": html.escape(source),
        "__DATA__": json.dumps(data, ensure_ascii=False),
    }.items():
        page = page.replace(token, value)
    return page


TEMPLATE = r"""<title>担当一覧表</title>
<style>
:root {
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
  --rank-a: #b3261e;
  --rank-b: #1f5aa6;
  --rank-c: #e8b923;
  --rank-d: #6b3fa0;
  --rank-kyu: #1f7a52;
  --rank-sup: #6b7785;
  /* ランク未設定。明暗どちらの地でも濃い文字が載るので 1 つで足りる。 */
  --rank-none: #9aa6b3;
  --badge-ink-strong: #ffffff;
  --badge-ink-pale: #16202b;
  --done: #b04a3f;
  --warn: #9a5b17;
  --btn-ink: #ffffff;
  --shadow: 0 1px 2px rgba(22, 32, 43, .06), 0 8px 24px rgba(22, 32, 43, .05);
  --gothic: "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Yu Gothic Medium", "Yu Gothic", "Noto Sans JP", "Meiryo", system-ui, sans-serif;
  --mincho: "Hiragino Mincho ProN", "Yu Mincho", "YuMincho", "Noto Serif JP", "MS PMincho", serif;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", "Roboto Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
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
    --rank-a: #f0918a;
    --rank-b: #7fb0e8;
    --rank-c: #e8c95a;
    --rank-d: #bfa0ea;
    --rank-kyu: #74c79c;
    --rank-sup: #a3aebb;
    --badge-ink-strong: #11161c;
    --badge-ink-pale: #11161c;
    --done: #d97b6d;
    --warn: #d8a25c;
    --btn-ink: #11161c;
    --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 24px rgba(0, 0, 0, .35);
  }
}
:root[data-theme="dark"] {
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
  --rank-a: #f0918a;
  --rank-b: #7fb0e8;
  --rank-c: #e8c95a;
  --rank-d: #bfa0ea;
  --rank-kyu: #74c79c;
  --rank-sup: #a3aebb;
  --badge-ink-strong: #11161c;
  --badge-ink-pale: #11161c;
  --done: #d97b6d;
  --warn: #d8a25c;
  --btn-ink: #11161c;
  --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 24px rgba(0, 0, 0, .35);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--gothic);
  font-size: 15px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.wrap {
  max-width: 1500px;
  margin: 0 auto;
  padding: 32px 20px 72px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── 表題 ─────────────────────────────── */
.masthead {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--ink);
}
.masthead h1 {
  font-family: var(--mincho);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 600;
  letter-spacing: .22em;
  margin: 0;
  text-wrap: balance;
}
.masthead .org {
  display: block;
  font-family: var(--gothic);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .18em;
  color: var(--ink-faint);
  margin-bottom: 6px;
}
.meta {
  font-size: 12px;
  color: var(--ink-soft);
  text-align: right;
  line-height: 1.9;
}
/* 年月と同期日は同じ書体・同じ大きさで組む */
.meta .era, .meta .synced {
  display: block;
  font-family: var(--mincho);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: .1em;
  color: var(--ink);
}
.meta code { font-family: var(--mono); font-size: 11px; color: var(--ink-faint); }

/* ── 集計 ─────────────────────────────── */
.stats-panel { border: none; }
.stats-panel > summary {
  display: flex;
  align-items: center;
  gap: 6px;
  width: fit-content;
  padding: 2px 4px 6px;
  font-size: 11px;
  letter-spacing: .14em;
  color: var(--ink-faint);
  cursor: pointer;
  list-style: none;
}
.stats-panel > summary::-webkit-details-marker { display: none; }
.stats-panel > summary::before {
  content: "▾";
  font-size: 10px;
  transition: transform .12s;
}
.stats-panel:not([open]) > summary::before { transform: rotate(-90deg); }
.stats-panel > summary:hover { color: var(--ink); }

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 1px;
  background: var(--rule);
  border: 1px solid var(--rule);
  border-radius: 3px;
  overflow: hidden;
}
.stat {
  background: var(--card);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: left;
  font: inherit;
  color: inherit;
  border: none;
}
.stat-label { font-size: 11px; letter-spacing: .14em; color: var(--ink-faint); }
.stat-value {
  font-family: var(--mono);
  font-variant-numeric: tabular-nums;
  font-size: 26px;
  line-height: 1.15;
  font-weight: 600;
}
button.stat { cursor: pointer; transition: background .12s; }
button.stat .stat-value {
  color: var(--seal);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
  width: fit-content;
}
button.stat:hover { background: var(--seal-soft); }
button.stat .stat-label::after { content: " ▸"; }

/* ── 操作 ─────────────────────────────── */
.controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 18px;
  padding: 14px 16px;
  background: var(--card);
  border: 1px solid var(--rule);
  border-radius: 3px;
  box-shadow: var(--shadow);
}
.control-group { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.control-group > .legend {
  font-size: 11px;
  letter-spacing: .14em;
  color: var(--ink-faint);
  margin-right: 2px;
}
.chip {
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
}
.chip:hover { border-color: var(--seal); }
.chip[aria-pressed="true"] { background: var(--seal-soft); border-color: var(--seal); color: var(--ink); }
.chip[aria-pressed="false"] { opacity: .45; text-decoration: line-through; }
.chip-count { font-family: var(--mono); font-variant-numeric: tabular-nums; font-size: 11px; color: var(--ink-faint); }
.swatch { width: 9px; height: 9px; border-radius: 2px; display: inline-block; }
.rank-a { background: var(--rank-a); }
.rank-b { background: var(--rank-b); }
.rank-c { background: var(--rank-c); }
.rank-d { background: var(--rank-d); }
.rank-kyu { background: var(--rank-kyu); }
.rank-sup { background: var(--rank-sup); }
.rank-none { background: var(--rank-none); }

.search {
  flex: 1 1 180px;
  min-width: 160px;
  font: inherit;
  font-size: 13px;
  padding: 6px 10px;
  border: 1px solid var(--rule-strong);
  border-radius: 3px;
  background: var(--card);
  color: var(--ink);
}
.search::placeholder { color: var(--ink-faint); }
.toggle { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--ink-soft); cursor: pointer; }
.toggle input { accent-color: var(--seal); }
:where(button, input, a, dialog):focus-visible { outline: 2px solid var(--seal); outline-offset: 2px; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font: inherit;
  font-size: 12.5px;
  padding: 5px 12px;
  border: 1px solid var(--seal);
  border-radius: 3px;
  background: var(--seal);
  color: var(--btn-ink);
  cursor: pointer;
  transition: filter .12s;
}
.btn:hover:not(:disabled) { filter: brightness(1.12); }
.btn:disabled { opacity: .5; cursor: progress; }
.btn.ghost { background: var(--card); color: var(--ink); border-color: var(--rule-strong); }
.btn.ghost:hover { border-color: var(--seal); }
.btn svg { width: 13px; height: 13px; fill: currentColor; }

/* ── 表 ───────────────────────────────── */
.sheet {
  background: var(--card);
  border: 1px solid var(--rule-strong);
  border-radius: 3px;
  box-shadow: var(--shadow);
  overflow: auto;
  max-height: 78vh;
}
table { border-collapse: separate; border-spacing: 0; width: max-content; min-width: 100%; font-size: 13px; }
th, td {
  border-right: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
  padding: 4px 8px;
  text-align: left;
  vertical-align: top;
  white-space: nowrap;
}
tbody td { min-width: 6.5em; }
thead th {
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
}
th.rowhead, thead th.corner {
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
}
thead th.corner { z-index: 4; }
th.col-count, td.col-count { text-align: right; background: var(--card-alt); }
th.col-cav, td.col-cav { border-left: 2px solid var(--rule-strong); }
tbody tr:nth-child(even) td:not(.col-count) { background: color-mix(in srgb, var(--card-alt) 55%, transparent); }
tbody tr.total th, tbody tr.total td {
  border-top: 2px solid var(--ink);
  background: var(--card-alt);
  font-weight: 600;
}
tbody tr.total td { text-align: right; }
.count { font-family: var(--mono); font-variant-numeric: tabular-nums; }
.count.zero { color: var(--ink-faint); font-weight: 400; }

/* ── セル ─────────────────────────────── */
.entry {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 2px 6px;
  padding: 1px 0;
  line-height: 1.45;
  max-width: 17em;
  white-space: normal;
  overflow-wrap: anywhere;
}
.entry + .entry { border-top: 1px dotted var(--rule); }
.entry .nm { flex: 0 1 auto; min-width: 0; }
.entry.is-dim { opacity: .22; }

/* 関与先名は Asana のタスクへのリンク。250 件並ぶので、下線は控えめにしておいて
   ホバー・フォーカスで確かめられる程度にする。 */
a.nm {
  color: inherit;
  text-decoration: underline;
  text-decoration-color: color-mix(in srgb, var(--seal) 32%, transparent);
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
  cursor: pointer;
}
a.nm:hover {
  color: var(--seal);
  text-decoration-color: currentColor;
}
.nm.is-done { color: var(--done); text-decoration: line-through; text-decoration-thickness: 1px; }
a.nm.is-done:hover { color: var(--done); }
.entry.is-hit .nm { background: color-mix(in srgb, var(--seal) 18%, transparent); border-radius: 2px; }
.badge {
  flex: none;
  font-family: var(--mono);
  font-size: 10px;
  line-height: 1.5;
  padding: 0 4px;
  border-radius: 2px;
  color: var(--badge-ink-strong);
  letter-spacing: .04em;
}
.badge.rank-c, .badge.rank-none { color: var(--badge-ink-pale); }
.others { flex: none; font-size: 10.5px; color: var(--ink-faint); }
/* 「他関与者を表示」を外したときは、一覧とドリルダウンの最終列ごと畳む。 */
body.no-others .rec-table th:last-child,
body.no-others .rec-table td:last-child { display: none; }

/* ── タブと各表示 ─────────────────────── */
.views { display: flex; flex-direction: column; }
.tabs { display: flex; flex-wrap: wrap; gap: 2px; }
.tab {
  font: inherit;
  font-size: 13px;
  padding: 7px 14px;
  border: 1px solid var(--rule-strong);
  border-bottom: none;
  border-radius: 3px 3px 0 0;
  background: var(--card-alt);
  color: var(--ink-soft);
  cursor: pointer;
  margin-bottom: -1px;
  transition: background .12s, color .12s;
}
.tab:hover { color: var(--ink); }
.tab[aria-selected="true"] {
  background: var(--card);
  color: var(--ink);
  font-weight: 600;
  position: relative;
  z-index: 1;
}
.tab-count { font-family: var(--mono); font-variant-numeric: tabular-nums; font-size: 11px; color: var(--ink-faint); margin-left: 7px; }
.views .sheet { border-radius: 0 3px 3px 3px; }
.caption {
  padding: 8px 12px;
  border-bottom: 1px solid var(--rule);
  background: var(--card-alt);
  font-size: 11.5px;
  color: var(--ink-faint);
  position: sticky;
  left: 0;
}
.sheet[hidden] { display: none; }
.list-view td.namecell { min-width: 240px; }
td.date { font-family: var(--mono); font-variant-numeric: tabular-nums; font-size: 12px; }

/* ── ダイアログ ───────────────────────── */
dialog {
  border: 1px solid var(--rule-strong);
  border-radius: 4px;
  background: var(--card);
  color: var(--ink);
  padding: 0;
  max-width: min(880px, 92vw);
  max-height: 86vh;
  box-shadow: 0 12px 48px rgba(0, 0, 0, .28);
}
dialog::backdrop { background: rgba(10, 16, 22, .55); }
.dlg-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--rule);
  position: sticky;
  top: 0;
  background: var(--card);
}
.dlg-head h2 {
  margin: 0;
  font-family: var(--mincho);
  font-size: 17px;
  font-weight: 600;
  letter-spacing: .1em;
}
.dlg-head .tally { font-family: var(--mono); font-size: 12px; color: var(--ink-faint); }
.dlg-body { padding: 0; overflow: auto; max-height: calc(86vh - 56px); }
.dlg-body table { font-size: 13px; }
.dlg-form { padding: 16px 18px; display: flex; flex-direction: column; gap: 12px; font-size: 13px; }
.dlg-form p { margin: 0; color: var(--ink-soft); line-height: 1.8; }
.dlg-form p.warn { color: var(--warn); }
.dlg-form label { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--ink-faint); }
.dlg-form label.inline { flex-direction: row; align-items: center; gap: 6px; font-size: 12.5px; color: var(--ink-soft); }
.dlg-form input[type="password"] {
  font: inherit;
  font-family: var(--mono);
  font-size: 13px;
  padding: 7px 10px;
  border: 1px solid var(--rule-strong);
  border-radius: 3px;
  background: var(--paper);
  color: var(--ink);
}
.dlg-form input[type="checkbox"] { accent-color: var(--seal); }
.dlg-form .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.dlg-form hr { border: none; border-top: 1px solid var(--rule); margin: 2px 0; width: 100%; }
.dlg-form .msg { font-size: 12.5px; min-height: 1.5em; }
.dlg-form .msg.err { color: var(--done); }
.dlg-form .msg.ok { color: var(--seal); }
.empty { padding: 24px 18px; color: var(--ink-faint); font-size: 13px; }

footer {
  font-size: 11.5px;
  color: var(--ink-faint);
  line-height: 1.9;
  border-top: 1px solid var(--rule);
  padding-top: 14px;
}
footer b { color: var(--ink-soft); }
@media (max-width: 720px) {
  .wrap { padding: 20px 12px 48px; }
  .meta { text-align: left; }
  .sheet { max-height: 70vh; }
}

/* ── 印刷・PDF ─────────────────────────── */
.print-note { display: none; }

@media print {
  /* 画面のテーマに関わらず白地・黒字で刷る */
  :root, :root[data-theme="dark"], :root:not([data-theme="light"]) {
    --paper: #ffffff;
    --card: #ffffff;
    --card-alt: #ffffff;
    --ink: #000000;
    --ink-soft: #333333;
    --ink-faint: #555555;
    --rule: #9aa6b2;
    --rule-strong: #55606b;
    --seal: #1b3f6b;
    --seal-soft: #ffffff;
    --rank-a: #b3261e;
    --rank-b: #1f5aa6;
    --rank-c: #e8b923;
    --rank-d: #6b3fa0;
    --rank-kyu: #1f7a52;
    --rank-sup: #6b7785;
    --badge-ink-strong: #ffffff;
    --badge-ink-pale: #000000;
    --done: #7a2f26;
    --shadow: none;
  }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body { background: #fff; }
  .wrap { max-width: none; padding: 0; gap: 10px; }
  .controls { display: none; }
  .tabs { display: none; }
  .stats-panel { display: none; }
  dialog { display: none; }
  .views .sheet { border-radius: 0; }
  .caption { position: static; border-color: var(--rule); }
  .print-note { display: inline; }
  .masthead { padding-bottom: 8px; }
  .masthead h1 { font-size: 24px; }
  footer { font-size: 9px; line-height: 1.6; }

  .sheet {
    max-height: none;
    overflow: visible;
    border: none;
    border-radius: 0;
    box-shadow: none;
  }
  thead { display: table-header-group; }
  tbody tr { break-inside: avoid; }
  thead th, th.rowhead, thead th.corner { position: static; }
  th, td { border-color: var(--rule); }
  a.nm { color: inherit; text-decoration: none; }
  a.nm.is-done { text-decoration: line-through; }

  /* マトリクスは 1 ページに収まるよう実測して縮小する（--print-scale は JS が入れる） */
  body:not(.mode-list) .sheet.matrix {
    width: calc(var(--pt-w, 100%) * var(--print-scale, 1));
    height: calc(var(--pt-h, auto) * var(--print-scale, 1));
    overflow: hidden;
  }
  body:not(.mode-list) #matrix {
    transform: scale(var(--print-scale, 1));
    transform-origin: top left;
  }
  body.mode-list td.namecell { white-space: normal; }
}
</style>

<div class="wrap">
  <header class="masthead">
    <h1><span class="org">税理士法人 福田会計</span>担当一覧表</h1>
    <div class="meta">
      <span class="era">__ERA__</span>
      <span class="synced" id="syncedAt"></span>
      <code>__SOURCE__</code>
    </div>
  </header>

  <details class="stats-panel" open>
    <summary>集計</summary>
    <section class="stats" id="stats" aria-label="集計"></section>
  </details>

  <section class="controls" aria-label="絞り込み">
    <div class="control-group">
      <span class="legend">ランク</span>
      <span id="rankChips" style="display:contents"></span>
    </div>
    <div class="control-group">
      <span class="legend">担当</span>
      <span id="staffChips" style="display:contents"></span>
    </div>
    <input class="search" type="search" id="q" placeholder="関与先名で検索" aria-label="関与先名で検索">
    <label class="toggle"><input type="checkbox" id="showOthers" checked> 他関与者を表示</label>
    <label class="toggle"><input type="checkbox" id="showDone"> 解約・完了済を表示</label>
    <button type="button" class="btn ghost" id="syncBtn">
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.5a6.5 6.5 0 0 1 5.9 3.8l1.4-.9V9h-4.2l1.5-1a4.9 4.9 0 0 0-9.1 1H1.9A6.5 6.5 0 0 1 8 1.5zm0 13a6.5 6.5 0 0 1-5.9-3.8L.7 11.6V7h4.2L3.4 8a4.9 4.9 0 0 0 9.1-1h1.6A6.5 6.5 0 0 1 8 14.5z"/></svg>
      Asanaと同期
    </button>
    <button type="button" class="btn" id="printBtn">
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 1h8v3H4zM2 5h12a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1h-2v3H4v-3H2a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm3 7h6v3H5zm7.5-5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5z"/></svg>
      印刷 / PDF保存
    </button>
  </section>

  <div class="views">
    <div class="tabs" id="tabs" role="tablist" aria-label="表示の切り替え"></div>

    <div class="sheet matrix" id="view-matrix" role="tabpanel">
      <table id="matrix">
        <thead><tr id="matrix-head"></tr></thead>
        <tbody id="matrix-body"></tbody>
      </table>
    </div>

    <div class="sheet list-view" id="view-list" role="tabpanel" hidden>
      <table id="list" class="rec-table">
        <thead><tr><th>決算月</th><th>関与先名</th><th>担当</th><th>ランク</th><th>他関与者</th></tr></thead>
        <tbody id="list-body"></tbody>
      </table>
    </div>

    <div class="sheet new-view" id="view-new" role="tabpanel" hidden>
      <p class="caption" id="newCaption"></p>
      <table id="newTable">
        <thead><tr><th>登録日</th><th>決算月</th><th>関与先名</th><th>担当</th><th>ランク</th><th>紹介チャネル</th></tr></thead>
        <tbody id="new-body"></tbody>
      </table>
    </div>
  </div>

  <footer>
    <b>件数</b>＝各決算月行の担当者列の合計（CAV列・補助業務行「補ー決算／補ー月次」を除く）。
    <b>合計</b>＝各列に載る全件数。<br>
    出典は Asana プロジェクト「40.税務業務：契約・提案用」のタスクと、カスタムフィールド「決算月」「ランク」「他関与者1」。
    列はタスクが属するセクション（担当者）。書式は SharePoint「30.担当一覧表」の月次 Excel に合わせています。<br>
    <b>関与先名</b>を押すと Asana のタスクが別のタブで開きます。<br>
    <b>新規タブ</b>の「登録日」は Asana にタスクが登録された日です。Asana に契約開始日の項目がないため、
    これを新規関与先の目安にしています。解約済の先を含めるには「解約・完了済を表示」を入れてください。<br>
    <span class="print-note">絞り込んだ状態のまま印刷しています。担当一覧表は A3 横 1 枚、その他のタブは A4 縦。</span>
  </footer>
</div>

<dialog id="drill">
  <div class="dlg-head">
    <h2 id="drillTitle"></h2>
    <span class="tally" id="drillTally"></span>
    <button type="button" class="btn ghost" id="drillClose">閉じる</button>
  </div>
  <div class="dlg-body" id="drillBody"></div>
</dialog>

<dialog id="syncDlg">
  <div class="dlg-head">
    <h2>Asana と同期</h2>
    <button type="button" class="btn ghost" id="syncClose">閉じる</button>
  </div>
  <div class="dlg-form">
    <p>プロジェクト「40.税務業務：契約・提案用」の最新のタスクを取り込み、この表を組み直します。
      トークンは Asana の［設定］→［アプリ］→［個人用アクセストークン］で作れます。</p>
    <label>個人用アクセストークン
      <input type="password" id="token" autocomplete="off" spellcheck="false" placeholder="2/1234567890/...">
    </label>
    <label class="inline"><input type="checkbox" id="remember"> このブラウザに保存する</label>
    <p class="warn">共用のパソコンでは保存しないでください。保存先はこのブラウザの localStorage です。</p>
    <div class="row">
      <button type="button" class="btn" id="doSync">同期する</button>
    </div>
    <hr>
    <p>ブラウザから Asana に直接つながらない環境では、書き出した JSON を読み込めます
      （<code>/tasks?project=…&amp;opt_fields=…</code> の応答。複数ページ分をまとめて選べます）。</p>
    <div class="row">
      <input type="file" id="jsonFile" accept=".json,.txt" multiple>
    </div>
    <p class="msg" id="syncMsg"></p>
  </div>
</dialog>

<script>
const DATA = __DATA__;

const RANK_CLASS = {"A": "a", "B": "b", "C": "c", "D": "d", "給": "kyu", "補ー決算": "sup", "補ー月次": "sup"};
const RANK_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "給": 4, "補ー決算": 5, "補ー月次": 6};
const NAME_PREFIX = /^(?:\[Duplicate\]\s*)?(?:\d{2}|個|給)_\s*/;
const NO_RANK = "―";
const MONTHS = DATA.baseRows.slice(0, 12);

const rankClass = r => "rank-" + (RANK_CLASS[r] || "none");
const rankOrder = r => [RANK_ORDER[r] === undefined ? 9 : RANK_ORDER[r], r];
const SUPPLEMENT = new Set(DATA.supplementRanks);
const ALL_COLUMNS = DATA.columns.concat([DATA.cavColumn]);
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"})[c]);

/* 集計タイル。pick を持つものは数字を押すと該当先の一覧を出す。 */
const STAT_DEFS = [
  {key: "total", label: "関与先件数",
   count: rs => rs.filter(r => r.col !== DATA.cavColumn && !SUPPLEMENT.has(r.rank)).length},
  {key: "staff", label: "担当者数",
   count: rs => new Set(rs.filter(r => DATA.columns.includes(r.col) && r.col !== DATA.inboxColumn).map(r => r.col)).size},
  {key: "rankA", label: "Aランク", pick: r => r.rank === "A" && r.col !== DATA.cavColumn},
  {key: "kyuyo", label: "給与計算", pick: r => r.rank === "給" && r.col !== DATA.cavColumn},
  {key: "cav", label: "CAV他関与", pick: r => r.col === DATA.cavColumn},
  {key: "inbox", label: "担当未割当", pick: r => r.col === DATA.inboxColumn},
];

const state = {
  ranks: new Set(),
  cols: new Set(ALL_COLUMNS),
  query: "",
  showDone: false,
  showOthers: true,
  tab: "matrix",
};

/* 和暦。令和は 2019 年から。 */
const wareki = year => year >= 2019 ? `令和${year - 2018}年` : `${year}年`;

/* 新規関与先の数え方は「件数」列と揃える（CAV他関与と補助業務行は除く）。 */
const isEngagement = r => r.col !== DATA.cavColumn && !SUPPLEMENT.has(r.rank);
const createdYear = r => r.created ? Number(r.created.slice(0, 4)) : null;

/* ── データ整形（Python 側の normalize() と同じ規則） ── */
function normalizeTasks(tasks) {
  const seen = new Set();
  const out = [];
  for (const t of tasks) {
    const gid = t.gid || t.name;
    if (seen.has(gid)) continue;
    seen.add(gid);

    let section = null;
    for (const m of t.memberships || []) {
      if (m && m.section && m.section.name) { section = m.section.name; break; }
    }
    const col = (DATA.columns.includes(section) && section !== DATA.inboxColumn) || section === DATA.cavColumn
      ? section : DATA.inboxColumn;

    const cf = name => {
      const f = (t.custom_fields || []).find(f => f && f.name === name);
      return f ? f.display_value : null;
    };
    const month = cf("決算月");
    let row;
    if (/^(?:[1-9]|1[0-2])$/.test(month || "")) row = month + "月";
    else if (["個人", "給(有)", "給(無)"].includes(month)) row = month;
    else row = DATA.unsetRow;

    out.push({
      name: String(t.name || "").replace(NAME_PREFIX, "").trim(),
      row, col,
      rank: cf("ランク") || "",
      others: cf("他関与者1") || "",
      done: !!t.completed,
      created: String(t.created_at || "").slice(0, 10),
      channel: cf("契約・紹介チャネル") || "",
      url: t.permalink_url || (t.gid ? `https://app.asana.com/0/${DATA.projectGid}/${t.gid}` : ""),
    });
  }
  const idx = r => {
    const i = DATA.baseRows.indexOf(r.row);
    return i === -1 ? 99 : i;
  };
  out.sort((a, b) => idx(a) - idx(b) || a.name.localeCompare(b.name, "ja"));
  return out;
}

/* ── 選択状態を保ったまま集計とチップを組み直す ── */
function liveRecords() { return DATA.records.filter(r => !r.done); }

/* チップの見出しは全レコードのランクから作る（ここに無いランクは表示できなくなる
   ため、CAV や解約済にしか出てこないランクも必ず並べる）。数字のほうは「件数」と
   同じ数え方に揃えて、有効な担当者列ぶんだけを数える。 */
function rankTally() {
  const tally = new Map();
  for (const r of DATA.records) tally.set(r.rank || NO_RANK, 0);
  for (const r of liveRecords()) {
    if (r.col === DATA.cavColumn) continue;
    const k = r.rank || NO_RANK;
    tally.set(k, tally.get(k) + 1);
  }
  return [...tally.entries()].sort((a, b) => {
    const [ao, ak] = rankOrder(a[0]), [bo, bk] = rankOrder(b[0]);
    return ao - bo || ak.localeCompare(bk, "ja");
  });
}

function renderChrome() {
  const tally = rankTally();
  const known = new Set(tally.map(([r]) => r));
  // 同期で増えたランクは表示、消えたランクは選択から落とす
  for (const [r] of tally) if (!state.ranks.has(r) && !state.seenRanks?.has(r)) state.ranks.add(r);
  for (const r of [...state.ranks]) if (!known.has(r)) state.ranks.delete(r);
  state.seenRanks = known;

  document.getElementById("rankChips").innerHTML = tally.map(([rank, count]) =>
    `<button type="button" class="chip" data-rank="${esc(rank)}" aria-pressed="${state.ranks.has(rank)}">` +
    `<span class="swatch ${rankClass(rank)}"></span>${esc(rank)}` +
    `<span class="chip-count">${count}</span></button>`
  ).join("");

  document.getElementById("staffChips").innerHTML = ALL_COLUMNS.map(col =>
    `<button type="button" class="chip" data-col="${esc(col)}" aria-pressed="${state.cols.has(col)}">${esc(col)}</button>`
  ).join("");

  const live = liveRecords();
  document.getElementById("stats").innerHTML = STAT_DEFS.map(def => {
    const value = def.pick ? live.filter(def.pick).length : def.count(live);
    const inner = `<span class="stat-label">${esc(def.label)}</span><span class="stat-value">${value}</span>`;
    return def.pick
      ? `<button type="button" class="stat" data-stat="${def.key}" title="${esc(def.label)}の関与先を一覧で表示">${inner}</button>`
      : `<div class="stat">${inner}</div>`;
  }).join("");
}

/* ── 表の描画 ── */
function visibleColumns() { return DATA.columns.filter(c => state.cols.has(c)); }

function tableRows() {
  const rows = DATA.baseRows.slice();
  if (DATA.records.some(r => r.row === DATA.unsetRow)) rows.push(DATA.unsetRow);
  return rows;
}

function activeRecords() {
  return DATA.records.filter(r =>
    (state.showDone || !r.done) &&
    state.ranks.has(r.rank || NO_RANK) &&
    state.cols.has(r.col)
  );
}

/* 関与先名は Asana のタスクへのリンク。permalink_url が取れていない古い書き出し
   では url が空になるので、そのときは素の文字として出す。 */
function nameHTML(rec) {
  const cls = "nm" + (rec.done ? " is-done" : "");
  const label = esc(rec.name);
  return rec.url
    ? `<a class="${cls}" href="${esc(rec.url)}" target="_blank" rel="noopener" title="Asana のタスクを開く：${label}">${label}</a>`
    : `<span class="${cls}">${label}</span>`;
}

function badgeHTML(rank) {
  return rank ? `<span class="badge ${rankClass(rank)}">${esc(rank)}</span>` : "";
}

function entryHTML(rec) {
  const hit = state.query && rec.name.toLowerCase().includes(state.query);
  const dim = state.query && !hit;
  const cls = ["entry", hit ? "is-hit" : "", dim ? "is-dim" : ""].filter(Boolean).join(" ");
  const others = rec.others && state.showOthers ? `<span class="others">＋${esc(rec.others)}</span>` : "";
  return `<div class="${cls}">${nameHTML(rec)}${badgeHTML(rec.rank)}${others}</div>`;
}

function renderMatrix() {
  const cols = visibleColumns();
  const showCav = state.cols.has(DATA.cavColumn);
  const recs = activeRecords();

  document.getElementById("matrix-head").innerHTML = ['<th class="corner">決算月</th>']
    .concat(cols.map(c => `<th>${esc(c)}</th>`))
    .concat(['<th class="col-count">件数</th>'])
    .concat(showCav ? [`<th class="col-cav">${esc(DATA.cavColumn)}</th>`] : [])
    .join("");

  const totals = {};
  ALL_COLUMNS.forEach(c => totals[c] = 0);
  let grand = 0;

  const body = tableRows().map(row => {
    const inRow = recs.filter(r => r.row === row);
    if (!inRow.length && !MONTHS.includes(row)) return "";
    let count = 0;
    const cells = cols.map(col => {
      const list = inRow.filter(r => r.col === col);
      totals[col] += list.length;
      count += list.filter(r => !SUPPLEMENT.has(r.rank)).length;
      return `<td>${list.map(entryHTML).join("")}</td>`;
    });
    grand += count;
    const cav = inRow.filter(r => r.col === DATA.cavColumn);
    totals[DATA.cavColumn] += cav.length;
    const cavCell = showCav ? `<td class="col-cav">${cav.map(entryHTML).join("")}</td>` : "";
    return `<tr><th class="rowhead">${esc(row)}</th>${cells.join("")}` +
      `<td class="col-count"><span class="count${count ? "" : " zero"}">${count}</span></td>${cavCell}</tr>`;
  }).join("");

  const totalRow = `<tr class="total"><th class="rowhead">合計</th>` +
    cols.map(c => `<td><span class="count">${totals[c]}</span></td>`).join("") +
    `<td class="col-count"><span class="count">${grand}</span></td>` +
    (showCav ? `<td class="col-cav"><span class="count">${totals[DATA.cavColumn]}</span></td>` : "") +
    `</tr>`;

  document.getElementById("matrix-body").innerHTML = body + totalRow;
}

function listRowHTML(r) {
  return `<tr><th class="rowhead">${esc(r.row)}</th>` +
    `<td class="namecell">${nameHTML(r)}</td>` +
    `<td>${esc(r.col)}</td>` +
    `<td>${badgeHTML(r.rank)}</td>` +
    `<td><span class="others">${esc(r.others)}</span></td></tr>`;
}

function renderList() {
  const recs = activeRecords().filter(r => !state.query || r.name.toLowerCase().includes(state.query));
  document.getElementById("list-body").innerHTML = recs.map(listRowHTML).join("");
}

/* ── 新規関与先タブ ── */
function newYears() {
  const years = new Set();
  for (const r of DATA.records) {
    const y = createdYear(r);
    if (y && isEngagement(r)) years.add(y);
  }
  return [...years].sort((a, b) => a - b).slice(-2);
}

function newRecords(year) {
  return activeRecords()
    .filter(r => isEngagement(r) && createdYear(r) === year)
    .filter(r => !state.query || r.name.toLowerCase().includes(state.query))
    .sort((a, b) => a.created.localeCompare(b.created) || a.name.localeCompare(b.name, "ja"));
}

function renderNew() {
  const year = Number(state.tab.replace("new", ""));
  if (!year) return;
  const recs = newRecords(year);
  document.getElementById("newCaption").textContent =
    `${wareki(year)}中に Asana に登録された関与先 ${recs.length} 件（登録日順）。` +
    `CAV他関与と補助業務行「補ー決算／補ー月次」は除いています。`;
  document.getElementById("new-body").innerHTML = recs.length
    ? recs.map(r =>
        `<tr><td class="date">${esc(r.created)}</td>` +
        `<th class="rowhead">${esc(r.row)}</th>` +
        `<td class="namecell">${nameHTML(r)}</td>` +
        `<td>${esc(r.col)}</td>` +
        `<td>${badgeHTML(r.rank)}</td>` +
        `<td><span class="others">${esc(r.channel)}</span></td></tr>`
      ).join("")
    : `<tr><td colspan="6"><p class="empty">該当する関与先はありません。</p></td></tr>`;
}

/* ── タブ ── */
function tabDefs() {
  return [
    {key: "matrix", label: "担当一覧表"},
    {key: "list", label: "一覧"},
    ...newYears().map(y => ({key: "new" + y, label: `${wareki(y)}新規`, count: newRecords(y).length})),
  ];
}

function renderTabs() {
  const defs = tabDefs();
  if (!defs.some(d => d.key === state.tab)) state.tab = "matrix";
  document.getElementById("tabs").innerHTML = defs.map(d =>
    `<button type="button" class="tab" role="tab" data-tab="${d.key}" aria-selected="${state.tab === d.key}">` +
    `${esc(d.label)}${d.count === undefined ? "" : `<span class="tab-count">${d.count}</span>`}</button>`
  ).join("");

  const isMatrix = state.tab === "matrix";
  document.body.classList.toggle("mode-list", !isMatrix);
  document.getElementById("view-matrix").hidden = !isMatrix;
  document.getElementById("view-list").hidden = state.tab !== "list";
  document.getElementById("view-new").hidden = !state.tab.startsWith("new");
}

document.getElementById("tabs").addEventListener("click", e => {
  const tab = e.target.closest(".tab");
  if (!tab) return;
  state.tab = tab.dataset.tab;
  render();
});

function render() {
  renderMatrix();
  renderList();
  renderNew();
  renderTabs();
}

function renderAll() { renderChrome(); render(); }

/* ── 集計タイルから該当先の一覧を開く ── */
const drill = document.getElementById("drill");

function openDrill(key) {
  const def = STAT_DEFS.find(d => d.key === key);
  if (!def || !def.pick) return;
  const recs = liveRecords().filter(def.pick);
  document.getElementById("drillTitle").textContent = def.label;
  document.getElementById("drillTally").textContent = `${recs.length} 件`;
  document.getElementById("drillBody").innerHTML = recs.length
    ? `<table class="rec-table"><thead><tr><th>決算月</th><th>関与先名</th><th>担当</th><th>ランク</th><th>他関与者</th></tr></thead>` +
      `<tbody>${recs.map(listRowHTML).join("")}</tbody></table>`
    : `<p class="empty">該当する関与先はありません。</p>`;
  drill.showModal();
}

document.getElementById("stats").addEventListener("click", e => {
  const tile = e.target.closest("button.stat");
  if (tile) openDrill(tile.dataset.stat);
});
document.getElementById("drillClose").addEventListener("click", () => drill.close());

/* ── 絞り込み ── */
document.getElementById("rankChips").addEventListener("click", e => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  const rank = chip.dataset.rank;
  const on = chip.getAttribute("aria-pressed") === "true";
  chip.setAttribute("aria-pressed", String(!on));
  on ? state.ranks.delete(rank) : state.ranks.add(rank);
  render();
});
document.getElementById("staffChips").addEventListener("click", e => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  const col = chip.dataset.col;
  const on = chip.getAttribute("aria-pressed") === "true";
  chip.setAttribute("aria-pressed", String(!on));
  on ? state.cols.delete(col) : state.cols.add(col);
  render();
});
document.getElementById("q").addEventListener("input", e => {
  state.query = e.target.value.trim().toLowerCase();
  render();
});
document.getElementById("showDone").addEventListener("change", e => {
  state.showDone = e.target.checked;
  render();
});
document.getElementById("showOthers").addEventListener("change", e => {
  state.showOthers = e.target.checked;
  document.body.classList.toggle("no-others", !state.showOthers);
  render();
});
/* ── 同期日の表示（年月と同じ和暦の組み方） ── */
function formatSynced(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return `Asana同期　${esc(iso)}`;
  const pad = n => String(n).padStart(2, "0");
  const era = d.getFullYear() >= 2019 ? `令和${d.getFullYear() - 2018}年` : `${d.getFullYear()}年`;
  return `Asana同期　${era}${d.getMonth() + 1}月${d.getDate()}日 ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function setSynced(iso) {
  DATA.synced = iso;
  document.getElementById("syncedAt").textContent = formatSynced(iso);
}

/* ── Asana と同期 ── */
const syncDlg = document.getElementById("syncDlg");
const syncMsg = document.getElementById("syncMsg");
const tokenInput = document.getElementById("token");
const rememberBox = document.getElementById("remember");
const doSyncBtn = document.getElementById("doSync");
const TOKEN_KEY = "asana-tantou-token";

function say(text, kind) {
  syncMsg.textContent = text;
  syncMsg.className = "msg" + (kind ? " " + kind : "");
}

async function fetchAllTasks(token) {
  const fields = "name,completed,memberships.section.name,custom_fields.name,custom_fields.display_value";
  let url = `https://app.asana.com/api/1.0/tasks?project=${DATA.projectGid}&limit=100&opt_fields=${encodeURIComponent(fields)}`;
  const tasks = [];
  for (let page = 1; url && page <= 50; page++) {
    say(`取得中… ${tasks.length} 件`);
    const res = await fetch(url, {headers: {Authorization: "Bearer " + token}});
    if (res.status === 401) throw new Error("トークンが受け付けられませんでした。個人用アクセストークンを確認してください。");
    if (!res.ok) throw new Error(`Asana から ${res.status} が返りました。`);
    const json = await res.json();
    tasks.push(...(json.data || []));
    url = json.next_page ? json.next_page.uri : null;
  }
  return tasks;
}

function applyTasks(tasks, label) {
  const records = normalizeTasks(tasks);
  if (!records.length) throw new Error("タスクが 1 件も読み取れませんでした。opt_fields が足りているか確認してください。");
  DATA.records = records;
  setSynced(new Date().toISOString());
  renderAll();
  say(`${label}：${records.length} 件を取り込みました。`, "ok");
}

doSyncBtn.addEventListener("click", async () => {
  const token = tokenInput.value.trim();
  if (!token) { say("トークンを入力してください。", "err"); return; }
  doSyncBtn.disabled = true;
  try {
    const tasks = await fetchAllTasks(token);
    applyTasks(tasks, "同期");
    if (rememberBox.checked) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch (err) {
    const offline = err instanceof TypeError;
    say(offline
      ? "Asana に接続できませんでした。社内ネットワークやブラウザの制限が原因のことがあります。下の JSON 読み込みをお使いください。"
      : err.message, "err");
  } finally {
    doSyncBtn.disabled = false;
  }
});

document.getElementById("jsonFile").addEventListener("change", async e => {
  const files = [...e.target.files];
  if (!files.length) return;
  try {
    const tasks = [];
    for (const file of files) {
      const payload = JSON.parse(await file.text());
      const page = Array.isArray(payload) ? payload : payload.data;
      if (!Array.isArray(page)) throw new Error(`${file.name} にタスクの配列が見つかりませんでした。`);
      tasks.push(...page);
    }
    applyTasks(tasks, `${files.length} ファイル読み込み`);
  } catch (err) {
    say(err.message, "err");
  } finally {
    e.target.value = "";
  }
});

document.getElementById("syncBtn").addEventListener("click", () => {
  const saved = localStorage.getItem(TOKEN_KEY);
  if (saved) { tokenInput.value = saved; rememberBox.checked = true; }
  say("");
  syncDlg.showModal();
});
document.getElementById("syncClose").addEventListener("click", () => syncDlg.close());

/* ── 印刷・PDF ──────────────────────────
   画面に出ている絞り込みのまま刷る。マトリクスは A3 横 1 枚に収まるよう
   実測して縮小し、一覧形式は A4 縦で見出し行を各ページに繰り返す。      */
const MM = 96 / 25.4;
const pageStyle = document.createElement("style");
document.head.appendChild(pageStyle);

function preparePrint() {
  if (document.body.classList.contains("mode-list")) {
    pageStyle.textContent = "@page { size: A4 portrait; margin: 12mm; }";
    return;
  }
  pageStyle.textContent = "@page { size: A3 landscape; margin: 10mm; }";
  const sheet = document.querySelector(".sheet.matrix");
  const table = document.getElementById("matrix");
  const w = table.scrollWidth, h = table.scrollHeight;

  // 表題と注記が使う高さを差し引いた残りに表を収める（集計は刷らないので数えない）。
  // 画面表示の実測なので、印刷時より大きめに出るぶん縮小率は安全側に振れる。
  const box = el => el ? el.getBoundingClientRect().height : 0;
  const gap = parseFloat(getComputedStyle(document.querySelector(".wrap")).rowGap) || 0;
  const reserve = box(document.querySelector(".masthead")) + box(document.querySelector("footer")) + gap * 2;

  // A3 横 420×297mm から余白 10mm×2 を引いた印刷可能域
  const scale = Math.min(1, (400 * MM) / w, Math.max(0.2, 277 * MM - reserve) / h);
  sheet.style.setProperty("--print-scale", scale);
  sheet.style.setProperty("--pt-w", w + "px");
  sheet.style.setProperty("--pt-h", h + "px");
}

window.addEventListener("beforeprint", preparePrint);
document.getElementById("printBtn").addEventListener("click", () => {
  preparePrint();
  window.print();
});

setSynced(DATA.synced);
renderAll();
</script>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Asana のタスクから担当一覧表 HTML を生成する")
    parser.add_argument("inputs", nargs="+", type=Path, help="Asana タスクの JSON ファイル")
    parser.add_argument("-o", "--output", type=Path, default=Path("担当一覧表.html"))
    parser.add_argument("--era", default="", help='表題横の年月（例: "令和8年8月度"）')
    parser.add_argument("--source", default="Asana / 40.税務業務：契約・提案用", help="出典の表示文字列")
    parser.add_argument("--synced", default="", help="Asana との同期日時（ISO 8601、既定は実行時刻）")
    args = parser.parse_args(argv)

    tasks = load_tasks(args.inputs)
    if not tasks:
        print("タスクが読み込めませんでした", file=sys.stderr)
        return 1

    records = normalize(tasks)
    now = dt.datetime.now()
    era = args.era or f"令和{now.year - 2018}年{now.month}月度"
    synced = args.synced or now.astimezone().isoformat(timespec="minutes")
    args.output.write_text(build_page(records, era, synced, args.source), encoding="utf-8")
    print(f"{args.output} を書き出しました（{len(records)} 件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
