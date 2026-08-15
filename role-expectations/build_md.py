#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""職階別の期待職能（税理士法人福田会計）の本文 Markdown を levels.py から生成する。

使い方: python3 build_md.py  → 職階別の期待職能.md
"""

from levels import DECISIONS, LEVELS, NOTES, RULES, VERSION, flag_of, is_prov

OUT = "職階別の期待職能.md"


def mark(item):
    text, flag = flag_of(item)
    return text + (f"　**【{flag}】**" if flag else "")


def numbered(items):
    return "\n".join(f"{i}. {mark(x)}" for i, x in enumerate(items, start=1))


def bulleted(items):
    return "\n".join(f"- {mark(x)}" for x in items)


def level_section(lv):
    head = lv["title"] if lv["sym"] == "―" else f"{lv['sym']}｜{lv['title']}"
    out = [f"### {head}（{lv['grades']}）", ""]
    out += [f"**テーマ：{lv['theme']}**", ""]

    if lv["revenue"] != "―":
        out += [
            f"| 期待売上高（年間） | 基本給レンジ | 新入年次／年齢の目安 |",
            "|---|---|---|",
            f"| {lv['revenue']} | {lv['salary']} | {lv['entry']} |",
            "",
        ]

    if lv["roster"]:
        who = "／".join(f"{n}（{g}）" for n, g in lv["roster"])
        out += [f"**在籍者**：{who}", ""]
    elif lv["sym"] not in ("―",):
        out += ["**在籍者**：現在なし（将来枠）", ""]

    def m(key):
        return "　**【仮】**" if is_prov(lv, key) else ""

    head = f"（{lv['promo_to']} へ）" if lv["promo_to"] else "（最上位）"
    out += [f"**昇格の条件{head}**{m('promo')}", bulleted(lv["promo"]), ""]

    if lv["role"]:
        tag = f" ＜{lv['role_tag']}＞" if lv["role_tag"] else ""
        out += [f"**期待される役割{tag}**{m('role')}", numbered(lv["role"]), ""]
    if lv["kpi1"]:
        out += [f"**測定指標1（関与先担当／フロントオフィス）**{m('kpi1')}",
                numbered(lv["kpi1"]), ""]
    if lv["kpi2"]:
        out += [f"**測定指標2（総務・経理／バックオフィス）**{m('kpi2')}",
                numbered(lv["kpi2"]), ""]
    if lv["process"]:
        out += [f"**期待されるプロセス**{m('process')}", numbered(lv["process"]), ""]
    if lv["input"]:
        out += [f"**必要なインプット**{m('input')}", bulleted(lv["input"]), ""]

    out.append("---")
    out.append("")
    return "\n".join(out)


def main() -> None:
    p = []
    p += [
        "# 職階別の期待職能（税理士法人福田会計）",
        "",
        f"**版数：{VERSION}（たたき台）**",
        "**原型：EMPグループ「給与テーブル期待職能（2024-09-01版）」**",
        "**連動資料：グレード制度 基本給テーブル（税理士法人福田会計）／賞与算定ロジック**",
        "",
        "> このファイルは `levels.py` から自動生成しています。",
        "> 内容を直すときは `levels.py` を編集して `python3 build_md.py` を実行してください。",
        "",
        "---",
        "",
        "## 0. この表の使い方",
        "",
        "- 「期待される役割」は、**そのグレードに在籍する人に求められる状態**を示す。"
        "昇格の可否は、下位グレードの期待される役割を**満たしていること**を前提に、"
        "上位グレードの「昇格の条件」で判定する。",
        "- **測定指標1** は関与先を担当する職員（フロントオフィス）、"
        "**測定指標2** は総務・経理（バックオフィス）に適用する。兼任者は両方を見る。",
        "- 半期（12月〜5月／6月〜11月）ごとの評価面談で、**この表の文言そのものを使って**"
        "フィードバックする。文言は直属上司が起案し、代表が承認、上司から本人へ通知する。",
        "- そのため上司は、日頃から部下を観察し、この表の項目で語れる状態にしておくこと。",
        "- **【要決定】** は制度自体が未整備の項目、**【仮】** は数値・条件が仮置きの項目。"
        "いずれも「4. 未確定・要決定事項」に対応する。",
        "",
        "---",
        "",
        f"## 1. 職階体系（福田会計 {len(LEVELS)} 段階）",
        "",
        "| 職階 | グレード | テーマ | 期待売上高（年間） | 基本給レンジ | 目安 |",
        "|---|---|---|---|---|---|",
    ]
    for lv in LEVELS:
        name = lv["title"] if lv["sym"] == "―" else f"{lv['title']}（{lv['sym']}）"
        p.append(
            f"| {name} | {lv['grades']} | {lv['theme']} "
            f"| {lv['revenue']} | {lv['salary']} | {lv['entry']} |"
        )
    p += [
        "",
        "※ 期待売上高＝基本給上限 × 2 × 1.3 × 1.15 × 14（千円未満切上）。"
        "「グレード制度 基本給テーブル」と一致。",
        "",
        "---",
        "",
        "## 2. 職階別 期待される役割",
        "",
    ]

    for lv in LEVELS:
        p.append(level_section(lv))

    p += ["## 3. 福田会計固有の運用ルール", ""]
    for i, r in enumerate(RULES, start=1):
        p += [f"### 3-{i}. {r['title']}", ""]
        if r["formula"]:
            p += ["```", r["formula"], "```", ""]
        for t in r["text"]:
            p += [t, ""]
        if r["lines"]:
            p += ["\n".join(f"- {x}" for x in r["lines"]), ""]

    p += ["---", "", "## 4. 未確定・要決定事項", ""]
    p += [
        "以下は EMP 版から福田会計版へ移す際に、**福田会計として決め切れていない**項目。"
        "運用開始前に代表決裁が必要。",
        "",
    ]
    for i, (title, body) in enumerate(DECISIONS, start=1):
        p.append(f"{i}. **{title}** — {body}")

    p += ["", "---", "", "## 5. 注記", ""]
    p += [f"- {n}" for n in NOTES]
    p.append("")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(p))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
