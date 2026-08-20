#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""職階別の期待職能（税理士法人福田会計）のスマホ閲覧用 HTML を levels.py から生成する。

1職階＝1スライド。横スワイプで職階を移動し、中身は縦スクロールする。
並びは下位から上位（T → EP）。実際に在籍している T・S・SS に先に着く。

使い方: python3 build_html.py  → 職階別の期待職能.html
"""

import html as _html

from atc_map import ATC_TOPICS, LINKS
from levels import (DECISIONS, LEVELS, REVISIONS, RULES, VERSION, flag_of,
                    grade_rows, is_prov, roster_by_grade, roster_names,
                    vacant_text)

# 一般版と管理者版の2本を出す。違いは「誰がどのグレードか」を出すかどうかだけ。
# 一般版のHTMLにはグレード別の在籍者を一切書き出さない（隠すのではなく持たせない）。
OUT = {
    False: "職階別の期待職能.html",
    True: "職階別の期待職能_管理者版.html",
}

# 管理者版から一般版へ渡すためのリンク。逆向きは張らない。
PUBLIC_URL = "https://claude.ai/code/artifact/8295227f-91f0-42ec-b096-de04999f8de0"

# この表を作った Claude Code セッション。表紙のサブタイトル直下に出す。
SESSION_URL = "https://claude.ai/code/session_01V97Y5cPta2HCqQvMyJKU9n"

SLUG = {
    "EP": "ep", "P": "p", "SD": "sd", "D": "d", "SM": "sm",
    "M": "m", "SS": "ss", "S": "s", "T": "t1",
}
LIGHT_TEXT_ON_BAND = {"EP", "P", "SD", "D", "SM", "M", "SS"}

CSS = """
  :root{
    --bg:#F6F7FA; --surface:#FFFFFF; --surface-2:#EFF2F7;
    --ink:#141A2B; --ink-2:#48526A; --ink-3:#79839A;
    --rule:#DDE2EC; --rule-soft:#E9EDF4;
    --accent:#8F6620; --flag:#A2382F; --flag-soft:#F7E6E3;

    /* rank ramp — deepest = most senior. carries the hierarchy in colour. */
    --r-ep:#16233F; --r-p:#1F3259;  --r-sd:#263D6B; --r-d:#2C4678;
    --r-sm:#35538D; --r-m:#3C5D97;  --r-ss:#5B7DB5; --r-s:#8CA6CC;
    --r-t1:#B7C7DE; --r-pre:#CBD3E0; --r-doc:#8F6620;

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
      --r-ep:#9FB6DD; --r-p:#92AAD7;  --r-sd:#869FD0; --r-d:#7A95CA;
      --r-sm:#6E8AC3; --r-m:#6280BC;  --r-ss:#5273AD; --r-s:#45659F;
      --r-t1:#3A5890; --r-pre:#334C7C; --r-doc:#D7AC63;
    }
  }
  :root[data-theme="dark"]{
    --bg:#0D111C; --surface:#151B2B; --surface-2:#1D2436;
    --ink:#E7EBF3; --ink-2:#A6B0C4; --ink-3:#77819A;
    --rule:#283044; --rule-soft:#232B3D;
    --accent:#D7AC63; --flag:#E3907F; --flag-soft:#2C1B18;
    --r-ep:#9FB6DD; --r-p:#92AAD7;  --r-sd:#869FD0; --r-d:#7A95CA;
    --r-sm:#6E8AC3; --r-m:#6280BC;  --r-ss:#5273AD; --r-s:#45659F;
    --r-t1:#3A5890; --r-pre:#334C7C; --r-doc:#D7AC63;
  }

  *{box-sizing:border-box;}
  html,body{height:100%;}
  body{
    margin:0;background:var(--bg);color:var(--ink);
    font-family:var(--gothic);font-size:16px;line-height:1.75;
    -webkit-text-size-adjust:100%;text-rendering:optimizeLegibility;
    height:100svh;display:flex;flex-direction:column;overflow:hidden;
  }

  /* ---- top bar: progress + jump chips ---- */
  .topbar{
    flex:none;background:var(--surface);border-bottom:1px solid var(--rule);
  }
  .progress{height:3px;background:var(--rule-soft);}
  .progress i{
    display:block;height:100%;width:0;background:var(--rank,var(--accent));
    transition:width .25s ease, background-color .25s ease;
  }
  .chips{
    display:flex;gap:.35rem;margin:0;padding:.5rem .8rem;list-style:none;
    overflow-x:auto;scrollbar-width:none;
  }
  .chips::-webkit-scrollbar{display:none;}
  .chips a{
    display:block;white-space:nowrap;text-decoration:none;
    padding:.24rem .6rem;border-radius:999px;border:1px solid var(--rule);
    background:var(--bg);color:var(--ink-3);
    font-family:var(--mono);font-size:.72rem;letter-spacing:.04em;
  }
  .chips a[aria-current="true"]{
    background:var(--chip,var(--accent));border-color:transparent;
    color:#fff;font-weight:700;
  }
  .chips a:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}

  /* ---- the deck ---- */
  .deck{
    flex:1;min-height:0;display:flex;
    overflow-x:auto;overflow-y:hidden;
    scroll-snap-type:x mandatory;scroll-behavior:smooth;
    scrollbar-width:none;overscroll-behavior-x:contain;
  }
  .deck::-webkit-scrollbar{display:none;}
  .slide{
    flex:0 0 100%;scroll-snap-align:start;scroll-snap-stop:always;
    overflow-y:auto;overscroll-behavior-y:contain;
    padding:1.5rem 1.1rem 3rem;
  }
  .inner{max-width:44rem;margin:0 auto;}

  /* ---- slide head ---- */
  .head{
    display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap;
    padding-bottom:.9rem;border-bottom:2px solid var(--rank);
  }
  .sym{
    font-family:var(--mono);font-size:.8rem;font-weight:700;letter-spacing:.08em;
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
  .head h2{
    font-family:var(--mincho);font-weight:600;font-size:1.7rem;
    margin:0;letter-spacing:.03em;line-height:1.25;
  }
  .head h2 .en{
    display:block;font-family:var(--mono);font-size:.66rem;
    letter-spacing:.14em;color:var(--ink-3);margin-top:.2rem;font-weight:400;
  }
  .grades{
    font-family:var(--mono);font-size:.78rem;color:var(--ink-3);
    margin:0 0 0 auto;letter-spacing:.03em;
  }
  .theme{
    font-family:var(--mincho);font-size:1.3rem;color:var(--ink);
    margin:1.1rem 0 0;letter-spacing:.04em;line-height:1.5;text-wrap:balance;
  }
  .theme .lbl{
    display:block;font-family:var(--mono);font-size:.6rem;
    letter-spacing:.16em;color:var(--ink-3);margin-bottom:.15rem;
  }

  /* figures */
  .figures{
    display:grid;grid-template-columns:1fr 1fr;gap:1px;
    margin:1.2rem 0 0;padding:0;
    background:var(--rule);border:1px solid var(--rule);
  }
  .figures>div{background:var(--surface);padding:.55rem .7rem;}
  .figures dt{
    font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;
    color:var(--ink-3);margin:0;
  }
  .figures dd{
    margin:.1rem 0 0;font-family:var(--mono);font-variant-numeric:tabular-nums;
    font-size:.92rem;color:var(--ink);letter-spacing:-.01em;
  }

  /* roster */
  .roster{
    display:flex;flex-wrap:wrap;align-items:center;gap:.35rem;
    margin:.9rem 0 0;font-size:.8rem;color:var(--ink-3);
  }
  .roster .lbl{font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;}
  .who{
    background:var(--surface-2);border:1px solid var(--rule);
    padding:.1rem .5rem;border-radius:999px;font-size:.78rem;color:var(--ink-2);
  }
  .who b{font-weight:600;color:var(--ink);}
  .who code{font-family:var(--mono);font-size:.66rem;color:var(--ink-3);margin-left:.25rem;}
  .vacant{color:var(--ink-3);font-size:.78rem;font-style:italic;}

  /* content blocks */
  .blk{margin:1.5rem 0 0;}
  .blk h3{
    font-family:var(--mono);font-size:.65rem;letter-spacing:.16em;
    color:var(--accent);margin:0 0 .45rem;font-weight:600;
  }
  .tag{
    display:inline-block;font-family:var(--mincho);font-size:.92rem;
    color:var(--ink-2);margin:0 0 .35rem;letter-spacing:.05em;
  }
  .blk ol,.blk ul{margin:0;padding-left:1.35rem;}
  .blk li{margin:.3rem 0;color:var(--ink-2);font-size:.94rem;line-height:1.7;}
  .blk li::marker{color:var(--ink-3);font-family:var(--mono);font-size:.8em;}
  .books{list-style:none;padding:0;display:flex;flex-direction:column;gap:.2rem;}
  .books li{padding-left:.9rem;position:relative;font-size:.9rem;}
  .books li::before{
    content:"";position:absolute;left:0;top:.72em;
    width:.35rem;height:1px;background:var(--ink-3);
  }
  .two{display:grid;gap:1.5rem;}
  @media (min-width:40rem){
    .two{grid-template-columns:1fr 1fr;}
    .figures{grid-template-columns:repeat(3,1fr);}
    .slide{padding:2rem 1.6rem 3rem;}
  }

  /* ATC の対応 */
  .atc{display:inline-flex;gap:.2rem;margin-left:.35rem;vertical-align:.05em;}
  .atc code{
    font-family:var(--mono);font-size:.58rem;letter-spacing:.04em;
    color:var(--accent);background:var(--surface-2);
    border:1px solid color-mix(in srgb, var(--accent) 35%, transparent);
    border-radius:2px;padding:.02rem .28rem;
  }
  .why{
    display:block;margin:.2rem 0 .5rem;font-size:.8rem;color:var(--ink-3);
    padding-left:.6rem;border-left:1px solid var(--rule);
  }
  .topics{display:flex;flex-direction:column;gap:.4rem;margin:0;padding:0;list-style:none;}
  .topics li{
    display:grid;grid-template-columns:2.4rem 1fr;gap:.6rem;align-items:baseline;
    background:var(--surface);border:1px solid var(--rule);
    border-left:3px solid var(--gcol,var(--accent));
    border-radius:2px;padding:.5rem .7rem;
  }
  .topics code{
    font-family:var(--mono);font-size:.66rem;font-weight:700;color:var(--gcol,var(--accent));
  }
  .topics b{display:block;font-size:.9rem;font-weight:600;margin-bottom:.1rem;}
  .topics span{display:block;font-size:.82rem;color:var(--ink-2);}
  .topics em{
    display:block;font-style:normal;font-family:var(--mono);
    font-size:.62rem;color:var(--ink-3);margin-top:.2rem;letter-spacing:.06em;
  }
  .grp{
    font-family:var(--mono);font-size:.62rem;letter-spacing:.16em;
    color:var(--ink-3);margin:1.4rem 0 .5rem;
  }
  .grp:first-of-type{margin-top:1rem;}

  .prov{
    display:inline-block;font-family:var(--mono);font-size:.6rem;
    letter-spacing:.1em;color:var(--flag);background:var(--flag-soft);
    border:1px solid color-mix(in srgb, var(--flag) 30%, transparent);
    padding:.02rem .35rem;border-radius:2px;margin-left:.35rem;
    vertical-align:.08em;white-space:nowrap;
  }

  /* ---- cover slide ---- */
  .cover{display:flex;flex-direction:column;justify-content:center;min-height:100%;}
  .kicker{
    font-family:var(--mono);font-size:.7rem;letter-spacing:.18em;
    color:var(--accent);text-transform:uppercase;margin:0 0 .9rem;
  }
  .cover h1{
    font-family:var(--mincho);font-weight:600;
    font-size:clamp(2.2rem,11vw,3.4rem);line-height:1.2;letter-spacing:.03em;
    margin:0;text-wrap:balance;
  }
  .cover .sub{
    font-family:var(--mincho);font-size:1.05rem;color:var(--ink-2);
    margin:.6rem 0 0;letter-spacing:.04em;
  }
  .cover .src{
    margin:.9rem 0 0;font-family:var(--mono);font-size:.72rem;
    letter-spacing:.04em;color:var(--ink-3);
  }
  .cover .src a{
    color:var(--accent);text-decoration:none;
    border-bottom:1px solid var(--rule);
    word-break:break-all;
  }
  .cover .src a:hover{border-bottom-color:var(--accent);}
  .cover .note{
    font-size:.85rem;color:var(--ink-2);margin:1.6rem 0 0;
    padding-left:.8rem;border-left:2px solid var(--accent);
  }
  .cover .note + .note{margin-top:.8rem;}
  .cover .meta{
    display:flex;flex-wrap:wrap;gap:.35rem .9rem;margin:1.8rem 0 0;
    font-family:var(--mono);font-size:.7rem;color:var(--ink-3);
  }
  .swipe{
    margin:2.2rem 0 0;font-family:var(--mono);font-size:.72rem;
    color:var(--ink-3);letter-spacing:.1em;
  }
  .todo{
    margin:1.8rem 0 0;padding:.9rem 1rem 1rem;
    background:var(--surface);border:1px solid var(--rule);
    border-left:3px solid var(--accent);border-radius:2px;
  }
  .todo .lbl{
    font-family:var(--mono);font-size:.6rem;letter-spacing:.16em;
    color:var(--accent);margin:0 0 .5rem;
  }
  .todo ul{margin:0;padding-left:1.1rem;}
  .todo li{font-size:.88rem;color:var(--ink);margin:.4rem 0;line-height:1.6;}
  .todo li::marker{color:var(--ink-3);}
  .todo li span{
    display:block;font-size:.76rem;color:var(--ink-3);margin-top:.1rem;
  }
  .warn{
    margin:1.2rem 0 0;padding:.7rem .9rem;
    background:var(--flag-soft);border-left:3px solid var(--flag);
    color:var(--ink);font-size:.85rem;
  }
  .warn b{color:var(--flag);font-weight:600;}
  .warn a{color:var(--flag);}

  /* ---- グレード表 ---- */
  .tbl-wrap{
    overflow-x:auto;margin:1.2rem 0 0;
    border:1px solid var(--rule);background:var(--surface);
  }
  table.gradetbl{
    border-collapse:collapse;width:100%;min-width:28rem;font-size:.84rem;
  }
  table.gradetbl th,table.gradetbl td{
    padding:.34rem .6rem;border-bottom:1px solid var(--rule-soft);
    text-align:left;white-space:nowrap;
  }
  table.gradetbl thead th{
    position:sticky;top:0;z-index:1;background:var(--surface-2);
    font-family:var(--mono);font-size:.58rem;letter-spacing:.11em;
    color:var(--ink-3);font-weight:600;border-bottom:1px solid var(--rule);
  }
  table.gradetbl thead th.num{text-align:right;}
  table.gradetbl tr.band th{
    background:var(--rank);color:#14203A;white-space:normal;
    font-family:var(--gothic);font-size:.8rem;font-weight:600;letter-spacing:.04em;
  }
  table.gradetbl tr.band.on-dark th{color:#FFFFFF;}
  :root[data-theme="dark"] table.gradetbl tr.band th,
  :root[data-theme="dark"] table.gradetbl tr.band.on-dark th{color:#0D111C;}
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]) table.gradetbl tr.band th,
    :root:not([data-theme="light"]) table.gradetbl tr.band.on-dark th{color:#0D111C;}
  }
  table.gradetbl tr.band th .g{
    font-family:var(--mono);font-size:.64rem;font-weight:400;
    opacity:.72;margin-left:.55rem;
  }
  table.gradetbl td.code{
    font-family:var(--mono);font-weight:700;font-size:.78rem;color:var(--ink);
  }
  table.gradetbl td.num{
    font-family:var(--mono);font-variant-numeric:tabular-nums;
    text-align:right;color:var(--ink-2);letter-spacing:-.01em;
  }
  table.gradetbl td.num i{font-style:normal;color:var(--ink-3);font-size:.9em;}
  table.gradetbl tr.here td{background:var(--flag-soft);}
  table.gradetbl td.who{font-size:.76rem;color:var(--ink-2);white-space:normal;}
  table.gradetbl td.who b{font-weight:600;color:var(--ink);}

  /* ---- rules / decisions slides ---- */
  .slide h2.sec{
    font-family:var(--mincho);font-size:1.7rem;font-weight:600;
    margin:0 0 .3rem;letter-spacing:.04em;
    padding-bottom:.9rem;border-bottom:2px solid var(--rank);
  }
  .lead{color:var(--ink-2);font-size:.88rem;margin:1rem 0 1.2rem;}
  .rule-card{
    background:var(--surface);border:1px solid var(--rule);
    border-radius:2px;padding:1rem 1rem 1.1rem;margin-bottom:.7rem;
  }
  .rule-card h3{
    font-family:var(--gothic);font-size:.98rem;font-weight:600;
    margin:0 0 .5rem;letter-spacing:.03em;
  }
  .rule-card p{margin:.3rem 0 0;color:var(--ink-2);font-size:.88rem;}
  .formula{
    font-family:var(--mono);font-size:.78rem;font-variant-numeric:tabular-nums;
    background:var(--surface-2);border:1px solid var(--rule-soft);
    padding:.6rem .7rem;margin:.2rem 0 .6rem;
    overflow-x:auto;white-space:pre;color:var(--ink);line-height:1.6;
  }
  .rule-card ul{margin:.4rem 0 0;padding-left:1.2rem;}
  .rule-card li{color:var(--ink-2);font-size:.86rem;margin:.2rem 0;}

  ol.decide{
    list-style:none;counter-reset:d;margin:0;padding:0;
    display:flex;flex-direction:column;gap:.5rem;
  }
  ol.decide li{
    counter-increment:d;position:relative;
    background:var(--surface);border:1px solid var(--rule);
    border-left:3px solid var(--flag);border-radius:2px;
    padding:.8rem 1rem .85rem 2.5rem;
  }
  ol.decide li::before{
    content:counter(d,decimal-leading-zero);
    position:absolute;left:.8rem;top:.9rem;
    font-family:var(--mono);font-size:.68rem;color:var(--flag);
  }
  ol.decide b{display:block;font-weight:600;font-size:.92rem;margin-bottom:.15rem;}
  ol.decide span{color:var(--ink-2);font-size:.85rem;}

  .colophon{
    margin-top:2rem;padding-top:1.2rem;border-top:1px solid var(--rule);
    font-family:var(--mono);font-size:.66rem;color:var(--ink-3);line-height:1.9;
  }
  .colophon p{margin:0 0 .2rem;}

  /* ---- pager ---- */
  .pager{
    flex:none;display:flex;align-items:center;gap:.6rem;
    padding:.5rem .8rem;background:var(--surface);
    border-top:1px solid var(--rule);
    padding-bottom:calc(.5rem + env(safe-area-inset-bottom));
  }
  .pager button{
    font:inherit;font-family:var(--mono);font-size:1rem;line-height:1;
    background:var(--bg);color:var(--ink-2);
    border:1px solid var(--rule);border-radius:2px;
    padding:.4rem .8rem;cursor:pointer;
  }
  .pager button:hover:not(:disabled){border-color:var(--accent);color:var(--accent);}
  .pager button:disabled{opacity:.35;cursor:default;}
  .pager button:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}
  .count{
    flex:1;text-align:center;font-family:var(--mono);
    font-size:.74rem;color:var(--ink-3);letter-spacing:.08em;
    font-variant-numeric:tabular-nums;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  }
  .count b{color:var(--ink);font-weight:600;}

  @media (prefers-reduced-motion:reduce){
    .deck{scroll-behavior:auto;}
    .progress i{transition:none;}
  }
"""

JS = """
  (function () {
    var deck = document.getElementById('deck');
    var slides = Array.prototype.slice.call(deck.querySelectorAll('.slide'));
    var chips = Array.prototype.slice.call(document.querySelectorAll('.chips a'));
    var bar = document.getElementById('bar');
    var label = document.getElementById('count');
    var prev = document.getElementById('prev');
    var next = document.getElementById('next');
    var topbar = document.getElementById('topbar');
    var current = -1;

    function show(i) {
      if (i === current) return;
      current = i;
      var slide = slides[i];
      var rank = getComputedStyle(slide).getPropertyValue('--rank');

      bar.style.width = ((i + 1) / slides.length * 100) + '%';
      topbar.style.setProperty('--rank', rank);
      label.innerHTML = '<b>' + (i + 1) + '</b> / ' + slides.length
        + '　' + (slide.dataset.label || '');
      prev.disabled = i === 0;
      next.disabled = i === slides.length - 1;

      chips.forEach(function (c) {
        var on = c.getAttribute('href') === '#' + slide.id;
        c.setAttribute('aria-current', on ? 'true' : 'false');
        if (on) {
          c.style.setProperty('--chip', rank.trim());
          c.scrollIntoView({ block: 'nearest', inline: 'nearest' });
        }
      });
    }

    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) show(slides.indexOf(e.target));
        });
      }, { root: deck, threshold: 0.55 });
      slides.forEach(function (s) { io.observe(s); });
    } else {
      deck.addEventListener('scroll', function () {
        show(Math.round(deck.scrollLeft / deck.clientWidth));
      });
    }

    function go(i) {
      i = Math.max(0, Math.min(slides.length - 1, i));
      deck.scrollTo({ left: i * deck.clientWidth, behavior: 'smooth' });
    }
    prev.addEventListener('click', function () { go(current - 1); });
    next.addEventListener('click', function () { go(current + 1); });

    chips.forEach(function (c) {
      c.addEventListener('click', function (ev) {
        ev.preventDefault();
        var t = document.getElementById(c.getAttribute('href').slice(1));
        if (t) go(slides.indexOf(t));
      });
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { go(current + 1); }
      else if (e.key === 'ArrowLeft') { go(current - 1); }
    });

    show(0);
  })();
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
        out.append(f"        <li>{esc(text)}{badge}</li>")
    out.append(f"      </{tag}>")
    return "\n".join(out)


def book_list(items):
    out = ['<ul class="books">']
    for b in items:
        out.append(f"        <li>{esc(b)}</li>")
    out.append("      </ul>")
    return "\n".join(out)


def process_block(lv, provisional=False):
    """期待されるプロセス。ATC対応がある行には記号チップとねらいを添える。"""
    if not lv["process"]:
        return ""
    linked = {proc: (codes, why) for proc, codes, why in LINKS.get(lv["sym"], [])}
    out = ["<ol>"]
    for item in lv["process"]:
        text, flag = flag_of(item)
        badge = f'<span class="prov">{esc(flag)}</span>' if flag else ""
        chips = why_html = ""
        if text in linked:
            codes, why = linked[text]
            chips = '<span class="atc">' + "".join(
                f"<code>{esc(c)}</code>" for c in codes
            ) + "</span>"
            why_html = f'<span class="why">{esc(why)}</span>'
        out.append(f"        <li>{esc(text)}{badge}{chips}{why_html}</li>")
    out.append("      </ol>")
    return block("期待されるプロセス", "\n".join(out), "", provisional)


def block(title, body, tag_text="", provisional=False):
    if not body:
        return ""
    tag = f'\n      <p class="tag">{esc(tag_text)}</p>' if tag_text else ""
    mark = '<span class="prov">仮</span>' if provisional else ""
    return (
        f'    <div class="blk">\n'
        f"      <h3>{esc(title)}{mark}</h3>{tag}\n"
        f"      {body}\n"
        f"    </div>"
    )


def nav_label(lv):
    """ページャ・チップに出す名前。入社前は記号（―）を出さない。"""
    return lv["title"] if lv["sym"] == "―" else f'{lv["sym"]} {lv["title"]}'


def level_slide(lv, admin=False):
    slug = SLUG[lv["sym"]]
    on_dark = " on-dark" if lv["sym"] in LIGHT_TEXT_ON_BAND else ""
    label = nav_label(lv)
    o = [
        f'<section class="slide lv-{slug}" id="{slug}" data-label="{esc(label)}"'
        f' style="--rank:var(--r-{slug})">',
        '  <div class="inner">',
        '    <div class="head">',
        f'      <span class="sym{on_dark}">{esc(lv["sym"])}</span>',
        f'      <h2>{esc(lv["title"])}<span class="en">{esc(lv["en"])}</span></h2>',
        f'      <p class="grades">{esc(lv["grades"])}</p>',
        "    </div>",
        f'    <p class="theme"><span class="lbl">テーマ</span>{esc(lv["theme"])}</p>',
    ]

    if lv["revenue"] != "―":
        o += [
            '    <dl class="figures">',
            f'      <div><dt>期待売上高</dt><dd>{esc(lv["revenue"])}</dd></div>',
            f'      <div><dt>基本給</dt><dd>{esc(lv["salary"])}</dd></div>',
            f'      <div><dt>目安</dt><dd>{esc(lv["entry"])}</dd></div>',
            "    </dl>",
        ]

    if lv["roster"]:
        chips = "".join(
            f'\n      <span class="who"><b>{esc(n)}</b>'
            + (f"<code>{esc(tag)}</code>" if tag else "")
            + "</span>"
            for n, tag in (lv["roster"] if admin else roster_names(lv))
        )
        o.append(f'    <p class="roster"><span class="lbl">在籍</span>{chips}\n    </p>')
    elif lv["sym"] != "―":
        o.append(
            '    <p class="roster"><span class="lbl">在籍</span>'
            f'<span class="vacant">{esc(vacant_text(lv))}</span></p>'
        )

    promo_title = (
        f'昇格の条件（{lv["promo_to"]} へ）' if lv["promo_to"] else "この上はない（最上位）"
    )
    for a, b in [
        (
            block("期待される役割", li_list(lv["role"]), lv["role_tag"],
                  is_prov(lv, "role")),
            block(promo_title, li_list(lv["promo"], "ul"), "",
                  is_prov(lv, "promo")),
        ),
        (
            block("測定指標1 ／ 関与先担当", li_list(lv["kpi1"]), "",
                  is_prov(lv, "kpi1")),
            block("測定指標2 ／ 総務・経理", li_list(lv["kpi2"]), "",
                  is_prov(lv, "kpi2")),
        ),
        (
            process_block(lv, is_prov(lv, "process")),
            block("必要なインプット", book_list(lv["input"]), "",
                  is_prov(lv, "input")),
        ),
    ]:
        if a or b:
            o.append('    <div class="two">')
            if a:
                o.append(a)
            if b:
                o.append(b)
            o.append("    </div>")

    o += ["  </div>", "</section>"]
    return "\n".join(o)


def grade_table(admin=False):
    """31グレードを1行ずつ並べた表。上（EP3）から下（T1）へ。

    admin=True のときだけ在籍列を付ける。一般版では列そのものを出さない。
    """
    who_of = roster_by_grade() if admin else {}
    ncol = 4 if admin else 3
    o = [
        '<div class="tbl-wrap">',
        '<table class="gradetbl">',
        "  <thead><tr>"
        "<th>グレード</th>"
        '<th class="num">基本給レンジ（月額）</th>'
        '<th class="num">期待売上高（年間）</th>'
        + ("<th>在籍</th>" if admin else "")
        + "</tr></thead>",
        "  <tbody>",
    ]
    for r in grade_rows():
        lv = r["level"]
        if r["first"]:
            dark = " on-dark" if r["sym"] in LIGHT_TEXT_ON_BAND else ""
            o.append(
                f'    <tr class="band{dark}" style="--rank:var(--r-{SLUG[r["sym"]]})">'
                f'<th colspan="{ncol}">{esc(lv["sym"])}｜{esc(lv["title"])}　'
                f'{esc(lv["theme"])}'
                f'<span class="g">入口の目安 {esc(lv["entry"])}</span></th></tr>'
            )
        pay = (
            f'<i>〜</i>{r["high"]:,}'
            if r["low"] is None
            else f'{r["low"]:,}<i>〜</i>{r["high"]:,}'
        )
        names = who_of.get(r["code"], [])
        cell = (
            '<td class="who">'
            + "／".join(f"<b>{esc(n)}</b>" for n in names)
            + "</td>"
            if admin
            else ""
        )
        here = ' class="here"' if names else ""
        o.append(
            f"    <tr{here}>"
            f'<td class="code">{esc(r["code"])}</td>'
            f'<td class="num">{pay} <i>円</i></td>'
            f'<td class="num">{r["revenue"]} <i>万円</i></td>{cell}</tr>'
        )
    o += ["  </tbody>", "</table>", "</div>"]
    return "\n".join(o)


def build(admin: bool) -> str:
    order = list(reversed(LEVELS))  # 下位から上位へ

    # チップの並びはスライドの並びと一致させる
    chips = [
        '<li><a href="#cover">表紙</a></li>',
        '<li><a href="#decide">要決定</a></li>',
        '<li><a href="#grades">グレード表</a></li>',
    ]
    chips += [
        f'<li><a href="#{SLUG[lv["sym"]]}">{esc(nav_label(lv))}</a></li>'
        for lv in order
    ]
    chips += [
        '<li><a href="#atc">ATC対応</a></li>',
        '<li><a href="#rules">運用ルール</a></li>',
    ]

    grades_tbl = grade_table(admin)

    rules = []
    for r in RULES:
        rules.append('    <div class="rule-card">')
        rules.append(f'      <h3>{esc(r["title"])}</h3>')
        for t in r["text"]:
            rules.append(f"      <p>{esc(t)}</p>")
        if r["formula"]:
            rules.append(f'      <div class="formula">{esc(r["formula"])}</div>')
        if r["lines"]:
            rules.append("      <ul>")
            rules += [f"        <li>{esc(x)}</li>" for x in r["lines"]]
            rules.append("      </ul>")
        rules.append("    </div>")

    GROUPS = [("選択理論の基礎", "A", "#4472C4"),
              ("目標達成技術", "B", "#8F6620"),
              ("対人関係・組織", "C", "#4B7B52")]
    used = {}
    for sym, rows in LINKS.items():
        for _, codes, _ in rows:
            for c in codes:
                used.setdefault(c, []).append(sym)
    sym_order = [lv["sym"] for lv in LEVELS]

    topics = []
    for gname, prefix, gcol in GROUPS:
        topics.append(f'    <p class="grp">{esc(gname)}</p>')
        topics.append('    <ul class="topics">')
        for code, (name, desc) in ATC_TOPICS.items():
            if not code.startswith(prefix):
                continue
            syms = sorted(set(used.get(code, [])), key=sym_order.index)
            topics.append(
                f'      <li style="--gcol:{gcol}"><code>{esc(code)}</code>'
                f"<div><b>{esc(name)}</b><span>{esc(desc)}</span>"
                f'<em>{esc(" / ".join(syms)) or "―"}</em></div></li>'
            )
        topics.append("    </ul>")

    decisions = "\n".join(
        f"      <li><b>{esc(t)}</b><span>{esc(b)}</span></li>" for t, b in DECISIONS
    )

    n_levels = len(LEVELS)
    revisions = (
        '<div class="todo">\n      <p class="lbl">改訂予定</p>\n      <ul>\n'
        + "\n".join(
            f"        <li>{esc(t)}<span>{esc(note)}</span></li>"
            for t, note in REVISIONS
        )
        + "\n      </ul>\n    </div>"
    )
    suffix = "（管理者版）" if admin else ""
    grade_note = (
        "色の付いた行に現在の在籍者がいます。"
        if admin
        else "誰がどのグレードかはこの表には出しません（在籍者は職階ごとのスライドに出ます）。"
    )
    banner = (
        '<p class="warn"><b>管理者版・取扱注意。</b>'
        "誰がどのグレードかを載せています。職員に見せる版は"
        f'<a href="{PUBLIC_URL}">こちら</a>で、そちらにはグレード別の在籍者を'
        "書き出していません。このページのリンクは配らないでください。</p>"
        if admin
        else ""
    )
    doc = f"""<title>【仕事】職階別の期待職能{suffix}</title>
<style>{CSS}</style>

<div class="topbar" id="topbar">
  <div class="progress"><i id="bar"></i></div>
  <ul class="chips">
    {chr(10).join('    ' + c for c in chips).strip()}
  </ul>
</div>

<div class="deck" id="deck" tabindex="0" aria-label="職階スライド">

<section class="slide" id="cover" data-label="表紙" style="--rank:var(--r-doc)">
  <div class="inner cover">
    <p class="kicker">税理士法人福田会計</p>
    <h1>【仕事】職階別の期待職能{suffix}</h1>
    <p class="sub">何を期待され、どう測られるか</p>
    <p class="src">作成経緯：<a href="{SESSION_URL}">Claude Code セッション</a></p>
    {banner}
    <p class="note">次が要決定事項、その次がグレード表（全31グレード）、その先が職階ごとのスライドです。並びは下から上（{esc(order[0]["title"])} → {esc(order[-1]["title"])}）。横にスワイプするか、上のチップから飛べます。</p>
    <p class="note">研究生（T1）が入口です。試用期間中もこの職階を見てください。</p>
    <p class="note">測定指標1は関与先を担当する職員、測定指標2は総務・経理に適用します。兼任者は両方を見ます。「要決定」「仮」の印は2ページ目に対応します。</p>
    {revisions}
    <div class="meta">
      <span>{esc(VERSION)}（たたき台）</span>
      <span>原型：EMPグループ 2024-09-01版</span>
      <span>全{n_levels}段階 / 31グレード</span>
    </div>
    <p class="swipe">SWIPE →</p>
  </div>
</section>

<section class="slide" id="decide" data-label="要決定" style="--rank:var(--r-doc)">
  <div class="inner">
    <h2 class="sec">運用開始前に決めること</h2>
    <p class="lead">EMP版から移す際に、福田会計として決め切れていない項目。各スライドの「要決定」「仮」の印はここに対応します。</p>
    <ol class="decide">
{decisions}
    </ol>
  </div>
</section>

<section class="slide" id="grades" data-label="グレード表" style="--rank:var(--r-doc)">
  <div class="inner">
    <h2 class="sec">グレード表</h2>
    <p class="lead">全31グレード。上ほど上位です。基本給レンジは月額、期待売上高は年間で、いずれも「グレード制度 基本給テーブル」と一致します。{grade_note}</p>
{grades_tbl}
    <p class="lead" style="margin-top:1.2rem">期待売上高＝そのグレードの基本給上限 × 2 × 1.3 × 1.15 × 14（千円未満切上）。各職階の「昇格の条件」は職階をまたぐときの判定です。同じ職階の中のグレード上げ（例：S3→S4）の基準は、この表にはまだありません。</p>
  </div>
</section>

{chr(10).join(level_slide(lv, admin) for lv in order)}

<section class="slide" id="atc" data-label="ATC対応" style="--rank:var(--r-doc)">
  <div class="inner">
    <h2 class="sec">アチーブメントとの対応</h2>
    <p class="lead">各職階の「期待されるプロセス」に付いている記号は、アチーブメントテクノロジー（ATC）の学習項目です。ATCは選択理論心理学（W.グラッサー）と成功哲学を土台に、実行力強化と習慣形成に特化した講座で、300の基礎技術で構成されます。記号の下の職階は、その技術を主に使う場面です。</p>
{chr(10).join(topics)}
    <p class="lead" style="margin-top:1.6rem">学習項目の並びはATCの講座順ではなく、この表のために系統立てたものです。実際の受講内容と突き合わせて確定させてください。ATC受講は現在 M（部長）の必要なインプットに置いていますが、技術自体は全職階で使います。</p>
  </div>
</section>

<section class="slide" id="rules" data-label="運用ルール" style="--rank:var(--r-doc)">
  <div class="inner">
    <h2 class="sec">運用ルール</h2>
    <p class="lead">グレード判定・賞与算定と直結する数値。基本給テーブルおよび賞与算定シートと一致させています。</p>
{chr(10).join(rules)}
    <div class="colophon">
      <p>税理士法人福田会計　期待職能　{esc(VERSION)}（たたき台）</p>
      <p>原型：EMPグループ「給与テーブル期待職能」2024-09-01版</p>
      <p>連動：グレード制度 基本給テーブル／賞与算定ロジック</p>
    </div>
  </div>
</section>

</div>

<div class="pager">
  <button id="prev" type="button" aria-label="前の職階">←</button>
  <span class="count" id="count"></span>
  <button id="next" type="button" aria-label="次の職階">→</button>
</div>

<script>{JS}</script>
"""
    return doc


def main() -> None:
    for admin in (False, True):
        with open(OUT[admin], "w", encoding="utf-8") as f:
            f.write(build(admin))
        print(f"wrote {OUT[admin]}")


if __name__ == "__main__":
    main()
