#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""期待職能（税理士法人福田会計版）のスマホ閲覧用 HTML を levels.py から生成する。

A3横1枚の一覧はスマホで読めないため、職階ごとのカードを縦に積んだ形にする。
並びは下位から上位（T1 → EP）。実際に在籍している T1・S・SS に先に着く。

使い方: python3 build_html.py  → 期待職能_福田会計.html
"""

import html as _html

from levels import DECISIONS, LEVELS, RULES, VERSION, flag_of

OUT = "期待職能_福田会計.html"

# 記号 → CSS クラス名 / 帯の上に白文字を置けるか
SLUG = {
    "EP": "ep", "P": "p", "SD": "sd", "D": "d", "SM": "sm",
    "M": "m", "SS": "ss", "S": "s", "T1": "t1", "―": "pre",
}
LIGHT_TEXT_ON_BAND = {"EP", "P", "SD", "D", "SM", "M", "SS"}

CSS = """
  /* ---- tokens: light (bare :root defines the full palette) ---- */
  :root{
    --bg:#F6F7FA;
    --surface:#FFFFFF;
    --surface-2:#EFF2F7;
    --ink:#141A2B;
    --ink-2:#48526A;
    --ink-3:#79839A;
    --rule:#DDE2EC;
    --rule-soft:#E9EDF4;
    --accent:#8F6620;
    --flag:#A2382F;
    --flag-soft:#F7E6E3;
    --shadow:0 1px 2px rgba(20,26,43,.05), 0 8px 24px -16px rgba(20,26,43,.28);

    /* rank ramp — deepest = most senior. carries the hierarchy in colour. */
    --r-ep:#16233F; --r-p:#1F3259;  --r-sd:#263D6B; --r-d:#2C4678;
    --r-sm:#35538D; --r-m:#3C5D97;  --r-ss:#5B7DB5; --r-s:#8CA6CC;
    --r-t1:#B7C7DE; --r-pre:#CBD3E0;

    --gothic:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic","YuGothic","Noto Sans JP","Meiryo",system-ui,sans-serif;
    --mincho:"Hiragino Mincho ProN","Yu Mincho","YuMincho","Noto Serif JP","MS PMincho",serif;
    --mono:ui-monospace,"SFMono-Regular","Menlo","Consolas",monospace;
  }
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]){
      --bg:#0D111C; --surface:#151B2B; --surface-2:#1D2436;
      --ink:#E7EBF3; --ink-2:#A6B0C4; --ink-3:#77819A;
      --rule:#283044; --rule-soft:#232B3D;
      --accent:#D7AC63; --flag:#E3907F; --flag-soft:#2C1B18;
      --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.8);
      --r-ep:#9FB6DD; --r-p:#92AAD7;  --r-sd:#869FD0; --r-d:#7A95CA;
      --r-sm:#6E8AC3; --r-m:#6280BC;  --r-ss:#5273AD; --r-s:#45659F;
      --r-t1:#3A5890; --r-pre:#334C7C;
    }
  }
  :root[data-theme="dark"]{
    --bg:#0D111C; --surface:#151B2B; --surface-2:#1D2436;
    --ink:#E7EBF3; --ink-2:#A6B0C4; --ink-3:#77819A;
    --rule:#283044; --rule-soft:#232B3D;
    --accent:#D7AC63; --flag:#E3907F; --flag-soft:#2C1B18;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.8);
    --r-ep:#9FB6DD; --r-p:#92AAD7;  --r-sd:#869FD0; --r-d:#7A95CA;
    --r-sm:#6E8AC3; --r-m:#6280BC;  --r-ss:#5273AD; --r-s:#45659F;
    --r-t1:#3A5890; --r-pre:#334C7C;
  }

  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{
    margin:0;background:var(--bg);color:var(--ink);
    font-family:var(--gothic);font-size:16px;line-height:1.75;
    -webkit-text-size-adjust:100%;text-rendering:optimizeLegibility;
  }
  .wrap{max-width:46rem;margin:0 auto;padding:0 1rem 5rem;}

  /* ---- masthead ---- */
  .mast{padding:2.5rem 0 1.5rem;}
  .kicker{
    font-family:var(--mono);font-size:.7rem;letter-spacing:.18em;
    color:var(--accent);text-transform:uppercase;margin:0 0 .9rem;
  }
  .mast h1{
    font-family:var(--mincho);font-weight:600;
    font-size:clamp(2rem,9vw,2.9rem);line-height:1.25;letter-spacing:.02em;
    margin:0;text-wrap:balance;
  }
  .mast .sub{
    font-family:var(--mincho);font-size:1rem;color:var(--ink-2);
    margin:.5rem 0 0;letter-spacing:.04em;
  }
  .mast .note{
    font-size:.82rem;color:var(--ink-2);margin:1rem 0 0;
    padding-left:.7rem;border-left:2px solid var(--accent);
  }
  .meta{
    display:flex;flex-wrap:wrap;gap:.4rem .9rem;margin:1.4rem 0 0;
    font-family:var(--mono);font-size:.72rem;color:var(--ink-3);
  }
  .meta span{white-space:nowrap;}

  /* ---- sticky jump rail ---- */
  nav.jump{
    position:sticky;top:0;z-index:20;
    margin:1.5rem -1rem 0;padding:.6rem 0;
    background:color-mix(in srgb, var(--bg) 88%, transparent);
    backdrop-filter:blur(10px);border-bottom:1px solid var(--rule);
  }
  nav.jump ul{
    display:flex;gap:.4rem;margin:0;padding:0 1rem;list-style:none;
    overflow-x:auto;scrollbar-width:none;
  }
  nav.jump ul::-webkit-scrollbar{display:none;}
  nav.jump a{
    display:block;white-space:nowrap;text-decoration:none;
    padding:.3rem .7rem;border-radius:999px;border:1px solid var(--rule);
    background:var(--surface);color:var(--ink-2);
    font-family:var(--mono);font-size:.75rem;letter-spacing:.04em;
  }
  nav.jump a:hover{border-color:var(--accent);color:var(--accent);}
  nav.jump a:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}

  /* ---- level cards ---- */
  .levels{display:flex;flex-direction:column;gap:1.1rem;margin-top:1.6rem;}
  .lv{
    position:relative;background:var(--surface);
    border:1px solid var(--rule);border-radius:2px;box-shadow:var(--shadow);
    padding:1.3rem 1.1rem 1.4rem 1.5rem;scroll-margin-top:4rem;overflow:hidden;
  }
  .lv::before{
    content:"";position:absolute;left:0;top:0;bottom:0;width:5px;
    background:var(--rank);
  }
  .lv-ep{--rank:var(--r-ep);}   .lv-p{--rank:var(--r-p);}
  .lv-sd{--rank:var(--r-sd);}   .lv-d{--rank:var(--r-d);}
  .lv-sm{--rank:var(--r-sm);}   .lv-m{--rank:var(--r-m);}
  .lv-ss{--rank:var(--r-ss);}   .lv-s{--rank:var(--r-s);}
  .lv-t1{--rank:var(--r-t1);}   .lv-pre{--rank:var(--r-pre);}

  .lv-head{display:flex;align-items:baseline;gap:.75rem;flex-wrap:wrap;}
  .sym{
    font-family:var(--mono);font-size:.78rem;font-weight:700;letter-spacing:.08em;
    background:var(--rank);color:#14203A;
    padding:.18rem .5rem;border-radius:2px;flex:none;
  }
  .sym.on-dark{color:#FFFFFF;}
  :root[data-theme="dark"] .sym,
  :root[data-theme="dark"] .sym.on-dark{color:#0D111C;}
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]) .sym,
    :root:not([data-theme="light"]) .sym.on-dark{color:#0D111C;}
  }
  .lv h2{
    font-family:var(--mincho);font-weight:600;font-size:1.5rem;
    margin:0;letter-spacing:.03em;line-height:1.3;
  }
  .lv h2 .en{
    display:block;font-family:var(--mono);font-size:.68rem;
    letter-spacing:.14em;color:var(--ink-3);margin-top:.15rem;font-weight:400;
  }
  .grades{
    font-family:var(--mono);font-size:.78rem;color:var(--ink-3);
    margin:0;letter-spacing:.03em;
  }
  .theme{
    font-family:var(--mincho);font-size:1.15rem;color:var(--ink);
    margin:.9rem 0 0;padding-left:.75rem;
    border-left:2px solid var(--rank);letter-spacing:.03em;
  }
  .theme .lbl{
    display:block;font-family:var(--mono);font-size:.6rem;
    letter-spacing:.16em;color:var(--ink-3);margin-bottom:.1rem;
  }

  /* figures strip */
  .figures{
    display:grid;grid-template-columns:1fr 1fr;gap:.1rem;
    margin:1.1rem 0 0;padding:0;
    background:var(--rule-soft);border:1px solid var(--rule-soft);
  }
  .figures>div{background:var(--surface);padding:.55rem .7rem;}
  .figures dt{
    font-family:var(--mono);font-size:.62rem;letter-spacing:.12em;
    color:var(--ink-3);margin:0;
  }
  .figures dd{
    margin:.1rem 0 0;font-family:var(--mono);font-variant-numeric:tabular-nums;
    font-size:.95rem;color:var(--ink);letter-spacing:-.01em;
  }
  .figures dd em{font-style:normal;font-size:.72rem;color:var(--ink-3);margin-left:.15rem;}

  /* roster */
  .roster{
    display:flex;flex-wrap:wrap;align-items:center;gap:.35rem;
    margin:.9rem 0 0;font-size:.8rem;color:var(--ink-3);
  }
  .roster .lbl{font-family:var(--mono);font-size:.62rem;letter-spacing:.12em;}
  .who{
    background:var(--surface-2);border:1px solid var(--rule);
    padding:.1rem .5rem;border-radius:999px;font-size:.78rem;color:var(--ink-2);
  }
  .who b{font-weight:600;color:var(--ink);}
  .who code{font-family:var(--mono);font-size:.68rem;color:var(--ink-3);margin-left:.25rem;}
  .vacant{color:var(--ink-3);font-size:.78rem;font-style:italic;}

  /* content blocks */
  .blk{margin:1.4rem 0 0;}
  .blk h3{
    font-family:var(--mono);font-size:.66rem;letter-spacing:.16em;
    color:var(--accent);margin:0 0 .45rem;font-weight:600;
  }
  .tag{
    display:inline-block;font-family:var(--mincho);font-size:.9rem;
    color:var(--ink-2);margin:0 0 .35rem;letter-spacing:.05em;
  }
  .blk ol,.blk ul{margin:0;padding-left:1.35rem;}
  .blk li{margin:.28rem 0;color:var(--ink-2);font-size:.94rem;line-height:1.7;}
  .blk li::marker{color:var(--ink-3);font-family:var(--mono);font-size:.8em;}
  .books{list-style:none;padding:0;display:flex;flex-direction:column;gap:.2rem;}
  .books li{padding-left:.9rem;position:relative;font-size:.88rem;}
  .books li::before{
    content:"";position:absolute;left:0;top:.72em;
    width:.35rem;height:1px;background:var(--ink-3);
  }
  .two{display:grid;gap:1.4rem;}
  @media (min-width:38rem){
    .two{grid-template-columns:1fr 1fr;}
    .figures{grid-template-columns:repeat(3,1fr);}
    .lv{padding:1.6rem 1.5rem 1.7rem 1.9rem;}
  }

  /* provisional flag */
  .prov{
    display:inline-block;font-family:var(--mono);font-size:.6rem;
    letter-spacing:.1em;color:var(--flag);background:var(--flag-soft);
    border:1px solid color-mix(in srgb, var(--flag) 30%, transparent);
    padding:.02rem .35rem;border-radius:2px;margin-left:.35rem;
    vertical-align:.08em;white-space:nowrap;
  }

  /* ---- rules / decisions ---- */
  .rules,.decide{margin-top:2.8rem;}
  .rules h2,.decide h2{
    font-family:var(--mincho);font-size:1.5rem;font-weight:600;
    margin:0 0 .3rem;letter-spacing:.04em;
  }
  .lead{color:var(--ink-2);font-size:.9rem;margin:0 0 1.2rem;}
  .rule-card{
    background:var(--surface);border:1px solid var(--rule);
    border-radius:2px;padding:1.1rem 1.1rem 1.2rem;margin-bottom:.8rem;
  }
  .rule-card h3{
    font-family:var(--gothic);font-size:1rem;font-weight:600;
    margin:0 0 .5rem;letter-spacing:.03em;
  }
  .rule-card p{margin:.3rem 0 0;color:var(--ink-2);font-size:.9rem;}
  .formula{
    font-family:var(--mono);font-size:.8rem;font-variant-numeric:tabular-nums;
    background:var(--surface-2);border:1px solid var(--rule-soft);
    padding:.6rem .7rem;margin:.2rem 0 .6rem;
    overflow-x:auto;white-space:pre;color:var(--ink);line-height:1.6;
  }
  .rule-card ul{margin:.4rem 0 0;padding-left:1.2rem;}
  .rule-card li{color:var(--ink-2);font-size:.88rem;margin:.2rem 0;}

  .decide ol{
    list-style:none;counter-reset:d;margin:0;padding:0;
    display:flex;flex-direction:column;gap:.55rem;
  }
  .decide li{
    counter-increment:d;position:relative;
    background:var(--surface);border:1px solid var(--rule);
    border-left:3px solid var(--flag);border-radius:2px;
    padding:.85rem 1rem .9rem 2.6rem;
  }
  .decide li::before{
    content:counter(d,decimal-leading-zero);
    position:absolute;left:.85rem;top:.95rem;
    font-family:var(--mono);font-size:.7rem;color:var(--flag);letter-spacing:.02em;
  }
  .decide b{display:block;font-weight:600;font-size:.94rem;margin-bottom:.15rem;}
  .decide span{color:var(--ink-2);font-size:.86rem;}

  footer{
    margin-top:3rem;padding-top:1.4rem;border-top:1px solid var(--rule);
    font-family:var(--mono);font-size:.68rem;color:var(--ink-3);line-height:1.9;
  }
  footer p{margin:0 0 .2rem;}
  @media (prefers-reduced-motion:reduce){
    *{animation:none !important;transition:none !important;scroll-behavior:auto !important;}
  }
"""


def esc(s):
    return _html.escape(str(s), quote=False)


def li_list(items, tag="ol"):
    if not items:
        return ""
    out = [f"<{tag}>"]
    for item in items:
        text, flag = flag_of(item)
        badge = f'<span class="prov">{esc(flag)}</span>' if flag else ""
        out.append(f"          <li>{esc(text)}{badge}</li>")
    out.append(f"        </{tag}>")
    return "\n".join(out)


def book_list(items):
    out = ['<ul class="books">']
    for b in items:
        out.append(f"          <li>{esc(b)}</li>")
    out.append("        </ul>")
    return "\n".join(out)


def block(title, body, tag_text=""):
    if not body:
        return ""
    tag = f'\n        <p class="tag">{esc(tag_text)}</p>' if tag_text else ""
    return (
        f'      <div class="blk">\n'
        f"        <h3>{esc(title)}</h3>{tag}\n"
        f"        {body}\n"
        f"      </div>"
    )


def card(lv):
    slug = SLUG[lv["sym"]]
    on_dark = ' on-dark' if lv["sym"] in LIGHT_TEXT_ON_BAND else ""
    o = [f'  <article class="lv lv-{slug}" id="{slug}">']
    o.append('    <div class="lv-head">')
    o.append(f'      <span class="sym{on_dark}">{esc(lv["sym"])}</span>')
    o.append(
        f'      <h2>{esc(lv["title"])}<span class="en">{esc(lv["en"])}</span></h2>'
    )
    o.append(f'      <p class="grades">{esc(lv["grades"])}</p>')
    o.append("    </div>")
    o.append(
        f'    <p class="theme"><span class="lbl">テーマ</span>{esc(lv["theme"])}</p>'
    )

    if lv["revenue"] != "―":
        o.append('    <dl class="figures">')
        o.append(
            f'      <div><dt>期待売上高</dt><dd>{esc(lv["revenue"])}</dd></div>'
        )
        o.append(f'      <div><dt>基本給</dt><dd>{esc(lv["salary"])}</dd></div>')
        o.append(f'      <div><dt>目安</dt><dd>{esc(lv["entry"])}</dd></div>')
        o.append("    </dl>")

    if lv["roster"]:
        chips = "".join(
            f'\n      <span class="who"><b>{esc(n)}</b><code>{esc(g)}</code></span>'
            for n, g in lv["roster"]
        )
        o.append(f'    <p class="roster"><span class="lbl">在籍</span>{chips}\n    </p>')
    elif lv["sym"] != "―":
        o.append(
            '    <p class="roster"><span class="lbl">在籍</span>'
            '<span class="vacant">現在なし（将来枠）</span></p>'
        )

    promo_title = (
        f'昇格の条件（{lv["promo_to"]} へ）' if lv["promo_to"] else "この上はない（最上位）"
    )
    pairs = [
        (
            block("期待される役割", li_list(lv["role"]), lv["role_tag"]),
            block(promo_title, li_list(lv["promo"], "ul")),
        ),
        (
            block("測定指標1 ／ 関与先担当", li_list(lv["kpi1"])),
            block("測定指標2 ／ 総務・経理", li_list(lv["kpi2"])),
        ),
        (
            block("期待されるプロセス", li_list(lv["process"])),
            block("必要なインプット", book_list(lv["input"])),
        ),
    ]
    for a, b in pairs:
        if a or b:
            o.append('    <div class="two">')
            if a:
                o.append(a)
            if b:
                o.append(b)
            o.append("    </div>")

    o.append("  </article>")
    return "\n".join(o)


def main() -> None:
    order = list(reversed(LEVELS))  # 下位から上位へ
    jump = "\n".join(
        f'    <li><a href="#{SLUG[lv["sym"]]}">{esc(lv["sym"])} {esc(lv["title"])}</a></li>'
        for lv in order
        if lv["sym"] != "―"
    )

    rules = []
    for r in RULES:
        rules.append('  <div class="rule-card">')
        rules.append(f'    <h3>{esc(r["title"])}</h3>')
        for t in r["text"]:
            rules.append(f"    <p>{esc(t)}</p>")
        if r["formula"]:
            rules.append(f'    <div class="formula">{esc(r["formula"])}</div>')
        if r["lines"]:
            rules.append("    <ul>")
            rules += [f"      <li>{esc(x)}</li>" for x in r["lines"]]
            rules.append("    </ul>")
        rules.append("  </div>")

    decisions = "\n".join(
        f"    <li><b>{esc(t)}</b><span>{esc(b)}</span></li>" for t, b in DECISIONS
    )

    doc = f"""<title>福田会計 期待職能</title>
<style>{CSS}</style>

<div class="wrap">

<header class="mast">
  <p class="kicker">税理士法人福田会計</p>
  <h1>期待職能</h1>
  <p class="sub">職階ごとに、何を期待されているか</p>
  <p class="note">測定指標1は関与先を担当する職員、測定指標2は総務・経理に適用します。兼任者は両方を見ます。「要決定」「仮」の印は末尾の決定事項に対応します。</p>
  <div class="meta">
    <span>{esc(VERSION)}（たたき台）</span>
    <span>原型：EMPグループ 2024-09-01版</span>
    <span>全{len(LEVELS) - 1}段階 / 31グレード</span>
  </div>
</header>

<nav class="jump" aria-label="職階へ移動">
  <ul>
{jump}
    <li><a href="#rules">運用ルール</a></li>
    <li><a href="#decide">要決定</a></li>
  </ul>
</nav>

<main class="levels">
{chr(10).join(card(lv) for lv in order)}
</main>

<section class="rules" id="rules">
  <h2>運用ルール</h2>
  <p class="lead">グレード判定・賞与算定と直結する数値。基本給テーブルおよび賞与算定シートと一致させています。</p>
{chr(10).join(rules)}
</section>

<section class="decide" id="decide">
  <h2>運用開始前に決めること</h2>
  <p class="lead">EMP版から移す際に、福田会計として決め切れていない項目。各カードの「要決定」「仮」の印はここに対応します。</p>
  <ol>
{decisions}
  </ol>
</section>

<footer>
  <p>税理士法人福田会計　期待職能　{esc(VERSION)}（たたき台）</p>
  <p>原型：EMPグループ「給与テーブル期待職能」2024-09-01版</p>
  <p>連動：グレード制度 基本給テーブル／賞与算定ロジック</p>
</footer>

</div>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
