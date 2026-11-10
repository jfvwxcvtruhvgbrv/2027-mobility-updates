"""정적 사이트 생성: data/reports/*.json → docs/ (GitHub Pages).

뉴스 에이전트 공통 규격(경제 사이트 기준): Pretendard 웹폰트, 종이색 바탕 + 카드, 영문 대문자 제목,
"2026년 11월 8일 일요일 · 00시 06분" 날짜 표기, 다크 모드 없음.
메인은 권역별 색으로 칠한 평면 세계지도(Equal Earth). 지역을 누르면 아래 목록이 걸러진다.
"""
import glob
import html
import json
import math
import os
from datetime import date as _date

import config

E = html.escape
TITLE = "WORLD MOBILITY UPDATES"
REGIONS = list(config.REGION_COLORS)            # 지도 7개 + 글로벌
MAP_REGIONS = [r for r in REGIONS if r != "글로벌"]
WEEK = "월화수목금토일"

FONT = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">'

CSS = """
:root{--paper:#E9EBEA;--card:#F7F8F6;--ink:#12151C;--ink-soft:#4B515C;--rule:#C8CCC4;--accent:#2a5bd7}
*{box-sizing:border-box}html{color-scheme:light}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 Pretendard,-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--ink)}.wrap{padding:40px 5vw 90px}
.brand{font-size:52px;font-weight:800;letter-spacing:-.01em;line-height:1.08;margin:0;text-transform:uppercase}
.brand a{text-decoration:none}
.topnav{display:flex;gap:18px;font-size:14px;margin:14px 0 0;flex-wrap:wrap}.topnav a{color:var(--ink-soft);text-decoration:none;border-bottom:1px solid var(--rule)}
.dateline{font-size:15px;color:var(--ink-soft);margin:22px 0 4px;font-weight:600}
.funnel{font-size:13px;color:var(--ink-soft)}
h2{font-size:23px;font-weight:800;margin:44px 0 12px;padding-top:14px;border-top:2px solid var(--ink);letter-spacing:-.01em}
h3{font-size:14px;color:var(--ink-soft);margin:22px 0 8px;font-weight:700}
.ops{font-size:13px;color:var(--ink-soft);font-weight:400}
/* map */
.hero{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:18px;margin-top:20px;align-items:start}
.mapcard{background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:14px 14px 10px}
.map{position:relative;width:100%}.map img,.map svg{display:block;width:100%;height:auto}
.map svg.overlay{position:absolute;inset:0}
.bub{cursor:pointer}.bub circle{transition:opacity .15s}.bub text{font:700 15px Pretendard,sans-serif;fill:var(--ink);pointer-events:none}
.bub .lab{font-size:13px;font-weight:600;fill:var(--ink-soft)}
.bub:focus{outline:none}.bub:focus circle,.bub:hover circle{stroke:var(--ink);stroke-width:2.5}
body[data-sel] .bub:not(.on) circle{opacity:.3}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:12px 2px 2px}
.chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--rule);background:var(--card);border-radius:99px;padding:4px 12px;font:600 13px Pretendard,sans-serif;color:var(--ink);cursor:pointer}
.chip.on{border-color:var(--ink);box-shadow:inset 0 0 0 1px var(--ink)}
.sw{width:10px;height:10px;border-radius:50%;display:inline-block;flex:none}
.selinfo{font-size:13px;color:var(--ink-soft);margin:8px 2px 0;min-height:20px}
/* top */
.side{display:flex;flex-direction:column;gap:18px}
.box{background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:16px 18px}
.box h4{margin:0 0 10px;font-size:14px;font-weight:700;color:var(--ink-soft)}.box ol{margin:0;padding-left:22px;font-size:17.5px;font-weight:500;line-height:1.6}.box ol li{margin-bottom:8px}.box ol li:first-child{font-size:20px;font-weight:800}
.flow{margin:0 0 16px;font-size:17.5px;font-weight:500;line-height:1.6}.flow b{display:block;font-size:24px;font-weight:800;line-height:1.3;margin-bottom:6px;letter-spacing:-.01em}.flow .refs a{font-size:12px;margin-right:6px;color:var(--ink-soft)}
nav.sec{position:sticky;top:0;background:var(--paper);border-bottom:1px solid var(--rule);padding:8px 0;z-index:5;display:flex;gap:8px;flex-wrap:wrap;margin-top:26px}
nav.sec a{font-size:13px;text-decoration:none;padding:3px 12px;border:1px solid var(--rule);border-radius:99px;background:var(--card)}
section,.card{scroll-margin-top:60px}
.filter{width:100%;padding:10px 14px;border:1px solid var(--rule);border-radius:8px;background:var(--card);color:var(--ink);font:15px Pretendard,sans-serif;margin:14px 0 4px}
/* cards */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;align-items:stretch}
.grid h3{grid-column:1/-1;margin:14px 0 0}
.card{background:var(--card);border:1px solid var(--rule);border-left:5px solid var(--rc,#4B515C);border-radius:10px;padding:14px 16px;margin:0;display:flex;flex-direction:column;font-size:15.5px;line-height:1.6}
.card h4{margin:0 0 6px;font-size:16.5px;line-height:1.45;font-weight:700}
.meta{font-size:13px;color:var(--ink-soft);display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.rchip{display:inline-flex;align-items:center;gap:5px;font-weight:700;color:var(--ink)}
.tag{background:var(--paper);border-radius:4px;padding:0 7px;font-size:12px;color:var(--ink);cursor:pointer}
.badge{border:1px solid var(--rule);border-radius:4px;padding:0 6px;font-size:11.5px;font-weight:700;color:var(--ink-soft)}
.b-new{border-color:#b3261e;color:#b3261e;cursor:pointer}.b-exp{border-color:#6250d6;color:#6250d6}
.card p{margin:8px 0}.why{font-size:14.5px;color:var(--ink-soft);border-left:2px solid var(--rule);padding-left:10px}
.links{font-size:13px;display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-top:auto;padding-top:8px}.links a{color:var(--ink-soft)}
.also{font-size:12.5px;color:var(--ink-soft);margin-top:4px}.also a{color:var(--ink-soft)}
.empty{font-size:13px;color:var(--ink-soft)}
.more h3{font-size:15px;color:var(--ink);margin:26px 0 4px}
.rbox{background:var(--card);border:1px solid var(--rule);border-top:4px solid var(--rc);border-radius:10px;padding:12px 18px 6px;margin:12px 0}
.rh{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:800;margin-bottom:2px}.rh .sw{background:var(--rc)}.rh .ops{font-weight:400}
.mlist{list-style:none;padding:0;margin:4px 0 0;display:grid;grid-template-columns:1fr;column-gap:32px}
@media(min-width:1100px){.mlist{grid-template-columns:1fr 1fr}}
.row{display:flex;align-items:baseline;gap:10px;padding:5px 0;border-bottom:1px solid var(--rule);font-size:14.5px;line-height:1.5;scroll-margin-top:60px;min-width:0}
.row .t{flex:1 1 auto;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-decoration:none;font-weight:500}.row .t:hover{text-decoration:underline}
.row .rm{order:2;flex:0 1 auto;max-width:42%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12.5px;color:var(--ink-soft)}
@media(max-width:600px){.row{flex-wrap:wrap;row-gap:0}.row .t{flex-basis:100%;white-space:normal}.row .rm{max-width:none;flex:1}}
.kind{font-size:11.5px;font-weight:700;border:1px solid var(--rule);border-radius:4px;padding:0 5px;color:var(--ink-soft)}
.rangebar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}.funnel,.dateline{max-width:none}
table.cov{border-collapse:collapse;font-size:13px;width:100%;background:var(--card)}table.cov td,table.cov th{border:1px solid var(--rule);padding:5px 8px;text-align:center}
table.cov td.zero{color:#b3261e;font-weight:700}table.cov th:first-child,table.cov td:first-child{text-align:left}
details summary{cursor:pointer;font-size:13px;color:var(--ink-soft)}
.arch{list-style:none;padding:0}.arch li{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:12px 16px;margin:8px 0}
.arch a{text-decoration:none}.arch .d{font-size:13px;color:var(--ink-soft);font-weight:600}.arch .h{font-weight:700;display:block}
footer{margin-top:60px;font-size:12.5px;color:var(--ink-soft);border-top:1px solid var(--rule);padding-top:12px}
@media(max-width:1100px){.hero{grid-template-columns:1fr}}
@media(max-width:600px){.wrap{padding:24px 16px 70px}.brand{font-size:32px}.grid{grid-template-columns:1fr}
 nav.sec{flex-wrap:nowrap;overflow-x:auto}nav.sec a{white-space:nowrap}.bub .lab{display:none}}
"""

PAGE_JS = """<script>
(function(){
const cards=[...document.querySelectorAll('.card[data-region],.row[data-region]')];
const q=document.getElementById('q');let sel=null;
function apply(){const v=q?q.value.trim().toLowerCase():'';let n=0;
 const hit=c=>v==='new'?c.dataset.new==='1':c.innerText.toLowerCase().includes(v);   // 'New' 검색 = New 배지 카드만
 cards.forEach(c=>{const ok=(!sel||c.dataset.region===sel)&&(!v||hit(c));c.style.display=ok?'':'none';if(ok)n++});
 document.querySelectorAll('section[data-area]').forEach(s=>{const vis=sel2=>[...s.querySelectorAll(sel2)].filter(c=>c.style.display!=='none').length;
  const a=vis('.card'),b=vis('.row');const cnt=s.querySelector('.cnt');if(cnt)cnt.textContent='총 '+(a+b)+'건 · 카드 '+a+' · 목록 '+b;
  const mh=s.querySelector('.more');if(mh)mh.style.display=b?'':'none';const mc=s.querySelector('.mcnt');if(mc)mc.textContent=b+'건';
  const em=s.querySelector('.empty');if(em)em.style.display=(a+b)?'none':''});
 document.querySelectorAll('.rbox').forEach(bx=>{const k=[...bx.querySelectorAll('.row')].filter(r=>r.style.display!=='none').length;bx.style.display=k?'':'none';const rn=bx.querySelector('.rn');if(rn)rn.textContent=k});
 document.querySelectorAll('h3[data-region]').forEach(h=>{let el=h.nextElementSibling,k=0;while(el&&el.classList.contains('card')){if(el.style.display!=='none')k++;el=el.nextElementSibling}h.style.display=k?'':'none'});
 const info=document.getElementById('selinfo');if(info)info.innerHTML=sel?('선택: <b>'+sel+'</b> '+n+'건 · <a href="#" id="clr">전체 보기</a>'):'지도의 원이나 아래 권역을 누르면 해당 지역 기사만 봅니다.';
 const clr=document.getElementById('clr');if(clr)clr.onclick=e=>{e.preventDefault();pick(null)};
}
function pick(r){sel=(sel===r)?null:r;if(sel)document.body.dataset.sel=sel;else delete document.body.dataset.sel;
 document.querySelectorAll('[data-pick]').forEach(b=>b.classList.toggle('on',b.dataset.pick===sel));apply();}
document.querySelectorAll('[data-pick]').forEach(b=>{b.addEventListener('click',()=>pick(b.dataset.pick));
 b.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick(b.dataset.pick)}})});
if(q)q.addEventListener('input',apply);
document.querySelectorAll('.tag,.b-new').forEach(t=>t.addEventListener('click',()=>{if(q){q.value=t.textContent;apply();q.scrollIntoView({behavior:'smooth'})}}));
apply();
})();
</script>"""


def repo():
    return os.environ.get("GITHUB_REPOSITORY") or config.DEFAULT_REPO


def pages_base():
    owner, name = repo().split("/", 1)
    return f"https://{owner.lower()}.github.io/{name}/"


def date_label(d, hhmm=None):
    y, m, dd = map(int, d.split("-"))
    s = f"{y}년 {m}월 {dd}일 {WEEK[_date(y, m, dd).weekday()]}요일"
    if hhmm:
        h, mi = hhmm.split(":")
        s += f" · {h}시 {mi}분"
    return s


def page(title, body, root="", script=True):
    nav = f'<nav class="topnav"><a href="{root}index.html">오늘의 리포트</a><a href="{root}archive.html">아카이브·검색</a></nav>'
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(title)}</title>{FONT}<style>{CSS}</style></head><body><div class="wrap">'
            f'<header><h1 class="brand"><a href="{root}index.html">{TITLE}</a></h1>{nav}</header>'
            f'{body}</div>{PAGE_JS if script else ""}</body></html>')


# ── 항목 정보 ────────────────────────────────────────────────────────────
COUNTRY_REGION = {c[0]: r for r, cs in config.REGIONS.items() for c in cs}


def region_of(it):
    for r in (it.get("story_region"), it.get("region")):
        if r in config.REGION_COLORS:
            return r
    return COUNTRY_REGION.get(it.get("country") or "", "글로벌")


def country_of(it):
    return it.get("story_country") or it.get("country") or ""


def item_title(it):
    return it.get("title_ko") or it.get("ko") or it.get("title") or ""


def row(it, date):
    reg = region_of(it)
    meta = " · ".join(x for x in (country_of(it), it.get("publisher") or "", (it.get("published") or "")[5:10]) if x)
    return (f'<li class="row" id="l-{E(it["id"])}" data-region="{E(reg)}" style="--rc:{config.REGION_COLORS[reg]}">'
            f'<a class="t" href="{E(it["url"])}" target="_blank" rel="noopener" title="{E(item_title(it))}">{E(item_title(it))}</a>'
            f'<span class="rm" title="{E(meta)}">{E(meta)}</span></li>')


def card(it, date):
    reg = region_of(it)
    col = config.REGION_COLORS[reg]
    badges = []
    if it.get("novel"):
        why_new = ", ".join(it.get("novel_entities") or []) or it.get("new_topic") or ""
        tip = f"아카이브에 처음 등장: {why_new}" if why_new else "아카이브에 처음 등장"
        badges.append(f'<span class="badge b-new" title="{E(tip)}">New</span>')
    if it.get("exploration"):
        badges.append('<span class="badge b-exp">탐색 표본</span>')
    tags = "".join(f'<span class="tag">{E(t)}</span>' for t in (it.get("tags") or []))
    if it.get("new_topic"):
        tags += f'<span class="tag">새 주제: {E(it["new_topic"])}</span>'
    also = ""
    if it.get("also"):
        also = '<div class="also">같은 사건 다른 보도: ' + ", ".join(
            f'<a href="{E(a["url"])}" rel="noopener" target="_blank">{E(a["publisher"])}</a>' for a in it["also"]) + "</div>"
    why = f'<p class="why">{E(it["why"])}</p>' if it.get("why") else ""
    authors = f' · {E(it["authors"])}' if it.get("authors") else ""
    cty = country_of(it)
    cty_s = f" · {E(cty)}" if cty and cty != reg else ""
    return (f'<article class="card" id="i-{it["id"]}" data-region="{E(reg)}" data-new="{1 if it.get("novel") else 0}" style="--rc:{col}"><h4>{E(it["title_ko"])}</h4>'
            f'<div class="meta"><span class="rchip"><span class="sw" style="background:{col}"></span>{E(reg)}</span>{cty_s} · {E(it["publisher"])}{authors} · '
            f'{E((it.get("published") or "")[:10])} {"".join(badges)}</div>'
            f'<p>{E(it["brief"])}</p>{why}<div class="meta">{tags}</div>'
            f'<div class="links"><a href="{E(it.get("resolved_url") or it["url"])}" target="_blank" rel="noopener">원문: {E(it["title"][:90])}</a>'
            f'</div>{also}</article>')


# ── 지도 ────────────────────────────────────────────────────────────────
def _world():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "world.json"), encoding="utf-8") as f:
        return json.load(f)


def world_svg():
    """권역별 색으로 칠한 베이스 지도 (모든 리포트가 공유하는 정적 파일)."""
    w = _world()
    paths = []
    for c in w["countries"]:
        if c["r"]:
            paths.append(f'<path d="{c["d"]}" fill="{config.REGION_COLORS[c["r"]]}" fill-opacity=".34"><title>{E(c["n"])} · {E(c["r"])}</title></path>')
        else:
            paths.append(f'<path d="{c["d"]}" fill="#D3D7D0"><title>{E(c["n"])} · 관찰 범위 밖</title></path>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w["W"]} {w["H"]}">'
            f'<path d="{w["sphere"]}" fill="#F7F8F6" stroke="#C8CCC4"/>'
            f'<g stroke="#F7F8F6" stroke-width=".6">{"".join(paths)}</g></svg>')


def map_block(items, root):
    w = _world()
    cnt = {r: 0 for r in REGIONS}
    for it in items:
        cnt[region_of(it)] += 1
    mx = max([cnt[r] for r in MAP_REGIONS] + [1])
    bubs = []
    for r in MAP_REGIONS:
        x, y = w["anchors"][r]
        n = cnt[r]
        rad = 12 + 24 * math.sqrt(n / mx) if n else 11
        col = config.REGION_COLORS[r]
        circle = (f'<circle r="{rad:.1f}" fill="{col}" fill-opacity=".92" stroke="#F7F8F6" stroke-width="2"/>' if n else
                  f'<circle r="{rad:.1f}" fill="#F7F8F6" stroke="{col}" stroke-width="2" stroke-dasharray="4 3"/>')
        bubs.append(f'<g class="bub" data-pick="{E(r)}" transform="translate({x},{y})" tabindex="0" role="button" aria-label="{E(r)} {n}건">'
                     f'{circle}<text text-anchor="middle" dy="5">{n}</text>'
                     f'<text class="lab" text-anchor="middle" y="{rad + 17:.0f}">{E(r)}</text></g>')
    chips = "".join(f'<button class="chip" data-pick="{E(r)}"><span class="sw" style="background:{config.REGION_COLORS[r]}"></span>{E(r)} {cnt[r]}</button>'
                    for r in REGIONS)
    return (f'<div class="mapcard"><div class="map"><img src="{root}assets/world.svg" alt="권역별로 색을 칠한 세계지도. 원의 크기는 오늘 분류된 사건 수"> '
            f'<svg class="overlay" viewBox="0 0 {w["W"]} {w["H"]}">{"".join(bubs)}</svg></div>'
            f'<div class="chips">{chips}</div><div class="selinfo" id="selinfo"></div>'
            f'<div class="ops" style="margin:2px">원 크기 = 오늘 수집·분류된 사건 수(카드+목록) · 점선 원 = 오늘 0건 · 회색 국가 = 아직 관찰 범위 밖 · 글로벌 = 논문·국제 행사 등 특정 국가 없는 자료</div></div>')


def coverage_table(items):
    cnt = {(r, a): 0 for r in REGIONS for a in config.AREAS}
    for it in items:
        cnt[(region_of(it), it["area"])] += 1
    head = "".join(f"<th>{E(v)}</th>" for v in config.AREAS.values())
    rows = "".join(f'<tr><td><span class="sw" style="background:{config.REGION_COLORS[r]}"></span> {E(r)}</td>'
                   + "".join(f'<td class="{"zero" if cnt[(r, a)] == 0 else ""}">{cnt[(r, a)]}</td>' for a in config.AREAS) + "</tr>"
                   for r in REGIONS)
    return f'<table class="cov"><tr><th>권역</th>{head}</tr>{rows}</table>'


# ── 리포트 본문 ──────────────────────────────────────────────────────────
def report_body(rep, root=""):
    date, items = rep["date"], rep["items"]
    listed = [x for x in rep.get("not_shown", []) if x.get("area") in config.AREAS]
    allitems = items + listed
    s = rep["stats"]
    out = [f'<div class="dateline">{E(date_label(date, rep.get("generated_kst")))}</div>'
           f'<div class="funnel">후보 {s["candidates"]}건 → 관련 {s["relevant"]}건 → 사건 {s["events"]}건 → 카드 {len(items)}건 · 목록 {len(listed)}건</div>',
           ]
    ov = rep.get("overview") or {}
    flows = ov.get("flows") or []
    flows_html = "".join(
        f'<div class="flow"><b>{E(f.get("title", ""))}</b>{E(f.get("text", ""))}<div class="refs">'
        + "".join(f'<a href="#i-{E(i)}">근거 {n + 1}</a>' for n, i in enumerate(f.get("ids", []))) + "</div></div>" for f in flows) \
        or '<p class="ops">오늘은 여러 시장을 가로지르는 뚜렷한 흐름이 없습니다.</p>'
    out.append(f'<div class="hero">{map_block(allitems, root)}<div class="side"><div class="box"><h4>오늘의 3가지</h4><ol>'
               + "".join(f"<li>{E(t)}</li>" for t in ov.get("top3", []))
               + f'</ol></div><div class="box"><h4>흐름</h4>{flows_html}</div></div></div>')
    secs = [(k, v) for k, v in config.AREAS.items()] + [("gaps", "범위·운영")]
    out.append('<nav class="sec">' + "".join(f'<a href="#s-{k}">{E(v)}</a>' for k, v in secs) + "</nav>")
    out.append('<input id="q" class="filter" placeholder="오늘 리포트 안에서 검색 — 카드와 더 많은 뉴스 목록 모두 (국가, 회사, 태그… · New = 처음 등장한 것만)">')
    for key, label in config.AREAS.items():
        group = [it for it in items if it["area"] == key]
        more = sorted((x for x in listed if x["area"] == key), key=lambda x: (REGIONS.index(region_of(x)), -(x.get("score") or 0)))
        out.append(f'<section id="s-{key}" data-area="{key}"><h2>{E(label)} <span class="ops cnt">총 {len(group) + len(more)}건 · 카드 {len(group)} · 목록 {len(more)}</span></h2>'
                   f'<p class="empty"{" style=display:none" if group or more else ""}>이 조건에 해당하는 기사가 없습니다.</p>')
        out.append('<div class="grid">')
        group.sort(key=lambda it: REGIONS.index(region_of(it)))   # 권역 순으로 이어 붙여 행을 끊지 않는다
        out.append("".join(card(it, date) for it in group))
        out.append("</div>")
        if more:
            boxes = []
            for reg in REGIONS:
                rr = [x for x in more if region_of(x) == reg]
                if rr:
                    boxes.append(f'<div class="rbox" style="--rc:{config.REGION_COLORS[reg]}"><div class="rh"><span class="sw"></span>{E(reg)}'
                                 f' <span class="ops">· <span class="rn">{len(rr)}</span>건</span></div>'
                                 f'<ul class="mlist">{"".join(row(x, date) for x in rr)}</ul></div>')
            out.append(f'<div class="more"><h3>더 많은 뉴스 <span class="ops mcnt">{len(more)}건</span></h3>{"".join(boxes)}</div>')
        out.append("</section>")
    fails = [x for x in rep["sources"] if not x["ok"]]
    zero = [x for x in rep["sources"] if x["ok"] and x["n"] == 0]
    out.append('<section id="s-gaps"><h2>범위·운영</h2><p class="ops">권역×분야별 사건 수(카드+목록). 0은 조사한 출처 범위 안에서 오늘 해당 자료가 없었다는 뜻입니다.</p>'
               + coverage_table(allitems))
    out.append(f'<p class="ops">출처 {len(rep["sources"])}개 중 접근 실패 {len(fails)}개, 결과 0건 {len(zero)}개.</p>')
    nb, na = sum(1 for x in items if x.get("basis") == "body"), sum(1 for x in items if x.get("basis") == "abstract")
    out.append(f'<p class="ops">카드 요약은 대부분 기사 제목·발췌 기준입니다 (본문 확보 {nb}/{len(items)}건'
               + (f", 논문 초록 {na}건" if na else "") + ').</p>'
               '<p class="ops"><span class="badge b-new">New</span> = 아카이브에 처음 등장한 제품·회사·소재·주제. 배지에 마우스를 올리면 무엇이 새로운지 보이고, 누르면 New 카드만 걸러집니다.</p>')
    if fails:
        out.append("<details><summary>접근 실패 출처</summary><ul class='ops'>" + "".join(f"<li>{E(x['source'])}: {E(x.get('error', ''))}</li>" for x in fails) + "</ul></details>")
    if zero:
        out.append("<details><summary>결과 0건 출처</summary><ul class='ops'>" + "".join(f"<li>{E(x['source'])}</li>" for x in zero) + "</ul></details>")
    held = rep.get("held", 0)
    out.append((f'<p class="ops">예산 상한으로 보류된 후보 {held}건은 다음 실행에서 처리합니다.</p>' if held else "") + "</section>")
    return "\n".join(out)


def load_reports():
    reps = []
    for p in sorted(glob.glob("data/reports/*.json"), reverse=True):
        with open(p, encoding="utf-8") as f:
            reps.append(json.load(f))
    return reps


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def headline(r):
    return ((r.get("overview") or {}).get("top3") or [""])[0]


def build_site():
    reps = load_reports()
    os.makedirs("docs/reports", exist_ok=True)
    write("docs/.nojekyll", "")
    write("docs/assets/world.svg", world_svg())
    for r in reps:
        write(f"docs/reports/{r['date']}.html", page(f"{TITLE} — {date_label(r['date'])}", report_body(r, "../"), "../"))
    if reps:
        write("docs/index.html", page(f"{TITLE} — {date_label(reps[0]['date'])}", report_body(reps[0])))
        latest = reps[0]
        write("docs/latest.json", json.dumps({
            "date": latest["date"], "generated_kst": latest["generated_kst"],
            "url": pages_base() + f"reports/{latest['date']}.html", "home": pages_base(),
            "top3": (latest.get("overview") or {}).get("top3", []),
            "counts": {k: sum(1 for i in latest["items"] + latest.get("not_shown", []) if i.get("area") == k) for k in config.AREAS},
            "regions": {r: sum(1 for i in latest["items"] + latest.get("not_shown", []) if region_of(i) == r) for r in REGIONS},
            "total": len(latest["items"]) + len(latest.get("not_shown", [])), "cards": len(latest["items"]), "novel": sum(1 for i in latest["items"] if i.get("novel")),
            "usd": latest.get("usage", {}).get("total_usd"),
        }, ensure_ascii=False, indent=1))
    else:
        write("docs/index.html", page(TITLE, "<p>아직 리포트가 없습니다.</p>"))

    # 아카이브 + 전체 검색: 월별 색인(docs/search/YYYY-MM.json), 기간 선택해서 필요한 달만 불러온다
    months = {}
    for r in reps:
        m = months.setdefault(r["date"][:7], [])
        for i in r["items"]:
            m.append({"d": r["date"], "id": i["id"], "k": "c", "t": i["title_ko"], "b": i["brief"][:160], "c": country_of(i),
                      "r": region_of(i), "a": i["area"], "tg": i.get("tags") or []})
        for i in r.get("not_shown", []):
            if i.get("area") in config.AREAS:
                m.append({"d": r["date"], "id": i["id"], "k": "l", "t": item_title(i), "c": country_of(i), "r": region_of(i),
                          "a": i["area"], "tg": i.get("tags") or [], "u": i["url"], "p": i.get("publisher") or ""})
    for mk, rows in months.items():
        write(f"docs/search/{mk}.json", json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    write("docs/search/months.json", json.dumps(sorted(months, reverse=True)))
    lst = "".join(f'<li><a href="reports/{r["date"]}.html"><span class="d">{E(date_label(r["date"], r.get("generated_kst")))}</span>'
                  f'<span class="h">{E(headline(r))}</span></a><span class="ops">카드 {len(r["items"])}건 · 목록 {len(r.get("not_shown", []))}건</span></li>' for r in reps)
    colors = json.dumps(config.REGION_COLORS, ensure_ascii=False)
    js = """<script>
const RC=""" + colors + """;const A={car:'자동차',mobility:'모빌리티',research:'리서치',event:'이벤트'};
const esc=s=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
const q=document.getElementById('aq'),o=document.getElementById('ares'),rg=document.getElementById('range'),st=document.getElementById('rstat');
const cache={};let MONTHS=[];
fetch('search/months.json').then(r=>r.json()).then(m=>{MONTHS=m;run()});
function pick(){const n=+rg.value;if(!n)return MONTHS;const [y,mo]=(MONTHS[0]||'2000-01').split('-').map(Number);
 const base=y*12+mo-1;return MONTHS.filter(k=>{const [a,b]=k.split('-').map(Number);return base-(a*12+b-1)<n})}
async function load(ms){await Promise.all(ms.filter(k=>!cache[k]).map(k=>fetch('search/'+k+'.json').then(r=>r.json()).then(d=>{cache[k]=d})));return ms.flatMap(k=>cache[k]||[])}
let tok=0;async function run(){const my=++tok;const ms=pick();const ix=await load(ms);if(my!==tok)return;
 st.textContent=ms.length+'개월 · '+ix.length.toLocaleString()+'건 색인';
 const v=q.value.trim().toLowerCase();if(v.length<2){o.innerHTML='';return}
 const hit=ix.filter(x=>(x.t+' '+(x.b||'')+' '+x.c+' '+x.r+' '+(x.p||'')+' '+x.tg.join(' ')).toLowerCase().includes(v));
 const show=hit.slice(0,300);
 o.innerHTML='<p class=ops>'+hit.length+'건'+(hit.length>300?' (앞 300건 표시)':'')+'</p>'+show.map(x=>x.k==='c'
  ?`<div class=card style="--rc:${RC[x.r]||'#4B515C'}"><h4><a href="reports/${x.d}.html#i-${x.id}">${esc(x.t)}</a></h4><div class=meta><span class=kind>카드</span> ${x.d} · ${esc(x.r)} · ${esc(x.c)} · ${A[x.a]||x.a}</div><p>${esc(x.b)}…</p></div>`
  :`<div class=card style="--rc:${RC[x.r]||'#4B515C'}"><h4><a href="${esc(x.u)}" target=_blank rel=noopener>${esc(x.t)}</a></h4><div class=meta><span class=kind>목록</span> ${x.d} · ${esc(x.r)} · ${esc(x.c)} · ${esc(x.p)} · ${A[x.a]||x.a} · <a href="reports/${x.d}.html#l-${x.id}">그날 리포트에서 보기</a></div></div>`).join('')}
q.addEventListener('input',run);rg.addEventListener('change',run);
</script>"""
    rng = ('<div class="rangebar"><label class="ops" for="range">기간</label><select id="range" class="chip">'
           '<option value="1">이번 달</option><option value="3" selected>최근 3개월</option><option value="6">최근 6개월</option>'
           '<option value="12">최근 1년</option><option value="36">최근 3년</option><option value="0">전체</option></select>'
           '<span class="ops" id="rstat"></span></div>')
    write("docs/archive.html", page(f"{TITLE} — 아카이브", f'<h2>아카이브·검색</h2>{rng}<input id="aq" class="filter" placeholder="검색어 (2글자 이상: 국가, 권역, 회사, 매체, 태그…) — 카드와 목록 모두">'
                                   f'<div id="ares"></div><h2>지난 리포트</h2><ul class="arch">{lst}</ul>{js}', script=False))


if __name__ == "__main__":
    build_site()
