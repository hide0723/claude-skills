#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""期待職能の本文を Asana のサブタスク説明欄と相互変換する。

運用の向き:
    Asana（正） → levels.py → md / xlsx / html

各職階が Asana の1サブタスクに対応し、その説明欄が下の書式を持つ。
所長が Asana を直せば、そこから levels.py の該当箇所を書き戻す。

    記号：SS
    職階：主任
    グレード：SS1〜SS6
    テーマ：どれだけ自走できるか

    ■期待される役割
    ＜自分で回し切る個人＞
    1. …
    2. …

    ■測定指標1（関与先担当）
    1. …

    ■測定指標2（総務・経理）
    1. …

    ■期待されるプロセス
    1. …

    ■昇格の条件（M へ）
    ・…

書式の約束:
  - 見出しは行頭の「■」。この行に【仮】が付くとセクション丸ごとが仮置き。
  - 項目行は「1. 」（順序あり）か「・」（順序なし）で始める。
  - 行末の【仮】【要決定】はその項目1件だけの印。
  - ＜…＞ の行は期待される役割の役割タグ。

Asana に載せないもの（levels.py のまま）:
  必要なインプット／期待売上高・基本給／在籍者／運用ルール／要決定事項／ATC対応

使い方:
    python3 asana_sync.py            # 全職階の説明文を書き出して往復テスト
    python3 asana_sync.py SS         # 1職階分だけ表示
"""

import re
import sys

from levels import LEVELS, flag_of, is_prov

# Asana 側の1タスク（この下に職階ごとのサブタスクがぶら下がる）
# プロジェクト「02.福田会計 目標設定／計画立案」＞ セクション「🏫人材」
#   ＞ 評価：💮「この評価・報酬を決めているのは自分」といえる評価制度（1213553428505834）
#     ＞ 評価ー役割：職務記述書を作成 ← ここ
PARENT_TASK_GID = "1210851805791807"

# 職階記号 → サブタスク GID。取り込みのときはこの表を使う。
SUBTASK_GID = {
    "T": "1217826872021676",
    "S": "1217826872285050",
    "SS": "1217826872284986",
    "M": "1217826824928404",
    "SM": "1217826913682537",
    "D": "1217826913873444",
    "SD": "1217826825288174",
    "P": "1217826895359525",
    "EP": "1217826872149932",
}

KPI1_HEAD = "測定指標1（関与先担当）"
KPI2_HEAD = "測定指標2（総務・経理）"

# 見出し → levels.py のキー、と項目の並べ方（"num" は 1. 、"dot" は ・）
SECTIONS = [
    ("期待される役割", "role", "num"),
    (KPI1_HEAD, "kpi1", "num"),
    (KPI2_HEAD, "kpi2", "num"),
    ("期待されるプロセス", "process", "num"),
    ("昇格の条件", "promo", "dot"),
]
HEAD_TO_KEY = {h: k for h, k, _ in SECTIONS}

FLAG_RE = re.compile(r"【(仮|要決定)】\s*$")
ITEM_RE = re.compile(r"^(?:\d+\.\s*|・)(.*)$")


# ---- levels.py → Asana ---------------------------------------------------

def _item_line(item, marker, i):
    text, flag = flag_of(item)
    head = f"{i}. " if marker == "num" else "・"
    return head + text + (f"　【{flag}】" if flag else "")


def to_notes(lv):
    """1職階分の説明文を組み立てる。"""
    out = [
        f"記号：{lv['sym']}",
        f"職階：{lv['title']}",
        f"グレード：{lv['grades']}",
        f"テーマ：{lv['theme']}",
    ]
    for head, key, marker in SECTIONS:
        items = lv[key]
        if not items:
            continue
        if key == "promo":
            head += f"（{lv['promo_to']} へ）" if lv["promo_to"] else "（最上位）"
        out += ["", "■" + head + ("　【仮】" if is_prov(lv, key) else "")]
        if key == "role" and lv["role_tag"]:
            out.append(f"＜{lv['role_tag']}＞")
        out += [_item_line(x, marker, i) for i, x in enumerate(items, start=1)]
    return "\n".join(out)


def subtask_name(lv):
    return f"{lv['sym']}｜{lv['title']}"


# ---- Asana → levels.py ---------------------------------------------------

def parse_notes(text):
    """説明文を dict に戻す。to_notes の逆。

    戻り値のキー: sym / title / grades / theme / role_tag / promo_to
    と、role・kpi1・kpi2・process・promo（項目のリスト）、prov（仮のキー）。
    項目は印がなければ文字列、あれば (本文, 印) のタプル。
    """
    out = {"role_tag": "", "promo_to": None, "prov": []}
    for key in HEAD_TO_KEY.values():
        out[key] = []

    key = None
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue

        if line.startswith("■"):
            head = line[1:].strip()
            if FLAG_RE.search(head):
                head = FLAG_RE.sub("", head).strip()
                prov = True
            else:
                prov = False
            m = re.match(r"^(昇格の条件)（(.+?)\s*へ）$", head)
            if m:
                head, out["promo_to"] = m.group(1), m.group(2).strip()
            elif head == "昇格の条件（最上位）":
                head, out["promo_to"] = "昇格の条件", None
            key = HEAD_TO_KEY.get(head)
            if key is None:
                raise ValueError(f"知らない見出し: {line}")
            if prov:
                out["prov"].append(key)
            continue

        if key is None:
            m = re.match(r"^(記号|職階|グレード|テーマ)：(.*)$", line)
            if m:
                field = {"記号": "sym", "職階": "title",
                         "グレード": "grades", "テーマ": "theme"}[m.group(1)]
                out[field] = m.group(2).strip()
            continue

        if line.startswith("＜") and line.endswith("＞"):
            out["role_tag"] = line[1:-1]
            continue

        m = ITEM_RE.match(line)
        if not m:
            raise ValueError(f"項目として読めない行: {line}")
        body = m.group(1).strip()
        fm = FLAG_RE.search(body)
        if fm:
            out[key].append((FLAG_RE.sub("", body).strip(), fm.group(1)))
        else:
            out[key].append(body)
    return out


# ---- 往復テスト ----------------------------------------------------------

def check_roundtrip():
    """全職階で to_notes → parse_notes が元に戻ることを確かめる。"""
    bad = []
    for lv in LEVELS:
        got = parse_notes(to_notes(lv))
        for field in ("sym", "title", "grades", "theme", "role_tag", "promo_to"):
            if got.get(field) != (lv[field] or (None if field == "promo_to" else "")):
                bad.append(f"{lv['sym']}.{field}: {got.get(field)!r} != {lv[field]!r}")
        for key in HEAD_TO_KEY.values():
            if got[key] != list(lv[key]):
                bad.append(f"{lv['sym']}.{key} が一致しない")
        if sorted(got["prov"]) != sorted(lv.get("prov", [])):
            bad.append(f"{lv['sym']}.prov: {got['prov']} != {lv.get('prov', [])}")
    return bad


def main() -> None:
    if len(sys.argv) > 1:
        want = sys.argv[1]
        for lv in LEVELS:
            if lv["sym"] == want:
                print(subtask_name(lv))
                print("-" * 40)
                print(to_notes(lv))
                return
        raise SystemExit(f"職階が見つからない: {want}")

    bad = check_roundtrip()
    if bad:
        print("往復テスト NG")
        for b in bad:
            print("  -", b)
        raise SystemExit(1)
    print(f"往復テスト OK（{len(LEVELS)}職階）")
    for lv in LEVELS:
        print(f"  {subtask_name(lv)}　{len(to_notes(lv))}字")


if __name__ == "__main__":
    main()
