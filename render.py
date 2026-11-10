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
import urllib.parse
from datetime import date as _date

import config

E = html.escape
TITLE = "2027 MOBILITY UPDATES"
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
.b-new{border-color:#b3261e;color:#b3261e}.b-exp{border-color:#6250d6;color:#6250d6}
.card p{margin:8px 0}.why{font-size:14.5px;color:var(--ink-soft);border-left:2px solid var(--rule);padding-left:10px}
.links{font-size:13px;display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-top:auto;padding-top:8px}.links a{color:var(--ink-soft)}
.also{font-size:12.5px;color:var(--ink-soft);margin-top:4px}.also a{color:var(--ink-soft)}
.pend{text-decoration:none;border:1px solid var(--ink);border-radius:6px;padding:2px 10px;color:var(--ink)!important;font-weight:600}
.empty{font-size:13px;color:var(--ink-soft)}.funnel,.dateline{max-width:none}
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
const cards=[...document.querySelectorAll('.card[data-region]')];
const q=document.getElementById('q');let sel=null;
function apply(){const v=q?q.value.trim().toLowerCase():'';let n=0;
 cards.forEach(c=>{const ok=(!sel||c.dataset.region===sel)&&(!v||c.innerText.toLowerCase().includes(v));c.style.display=ok?'':'none';if(ok)n++});
 document.querySelectorAll('section[data-area]').forEach(s=>{const k=[...s.querySelectorAll('.card')].filter(c=>c.style.display!=='none').length;
  const cnt=s.querySelector('.cnt');if(cnt)cnt.textContent=k+'건';const em=s.querySelector('.empty');if(em)em.style.display=k?'none':''});
 document.querySelectorAll('h3[data-region]').forEach(h=>{let el=h.nextElementSibling,k=0;while(el&&el.classList.contains('card')){if(el.style.display!=='none')k++;el=el.nextElementSibling}h.style.display=k?'':'none'});
 const info=document.getElementById('selinfo');if(info)info.innerHTML=sel?('선택: <b>'+sel+'</b> '+n+'건 · <a href="#" id="clr">전체 보기</a>'):'지도의 원이나 아래 권역을 누르면 해당 지역 기사만 봅니다.';
 const clr=document.getElementById('clr');if(clr)clr.onclick=e=>{e.preventDefault();pick(null)};
}
function pick(r){sel=(sel===r)?null:r;if(sel)document.body.dataset.sel=sel;else delete document.body.dataset.sel;
 document.querySelectorAll('[data-pick]').forEach(b=>b.classList.toggle('on',b.dataset.pick===sel));apply();}
document.querySelectorAll('[data-pick]').forEach(b=>{b.addEventListener('click',()=>pick(b.dataset.pick));
 b.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick(b.dataset.pick)}})});
if(q)q.addEventListener('input',apply);
document.querySelectorAll('.tag').forEach(t=>t.addEventListener('click',()=>{if(q){q.value=t.textContent;apply();q.scrollIntoView({behavior:'smooth'})}}));
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
    nav = (f'<nav class="topnav"><a href="{root}index.html">오늘의 리포트</a><a href="{root}archive.html">아카이브·검색</a>'
           f'<a href="{root}pending.html">심층 대기 목록</a></nav>')
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(title)}</title>{FONT}<style>{CSS}</style></head><body><div class="wrap">'
            f'<header><h1 class="brand"><a href="{root}index.html">{TITLE}</a></h1>{nav}</header>'
            f'{body}</div>{PAGE_JS if script else ""}</body></html>')


# ── 항목 정보 ────────────────────────────────────────────────────────────
def region_of(it):
    r = it.get("story_region")
    return r if r in config.REGION_COLORS else (it.get("region") if it.get("region") in config.REGION_COLORS else "글로벌")


def country_of(it):
    return it.get("story_country") or it.get("country") or ""


def issue_link(it, date):
    body = (f"id: {it['id']}\n리포트: {date}\n원문: {it.get('resolved_url') or it['url']}\n"
            f"국가: {country_of(it)} / 매체: {it['publisher']}\n분야: {config.AREAS.get(it['area'], it['area'])}\n\n"
            f"단신:\n{it['brief']}\n\n심층 조사에서 보고 싶은 점(선택):\n")
    q = urllib.parse.urlencode({"labels": config.PENDING_LABEL, "title": f"[심층] {it['title_ko']}", "body": body})
    return f"https://github.com/{repo()}/issues/new?{q}"


BASIS = {"body": "본문 기반", "snippet": "헤드라인·요약 기반", "abstract": "초록 기반"}


def card(it, date):
    reg = region_of(it)
    col = config.REGION_COLORS[reg]
    badges = []
    if it.get("novel"):
        label = "처음 보는 것" + (": " + ", ".join(it.get("novel_entities", [])[:2]) if it.get("novel_entities") else "")
        badges.append(f'<span class="badge b-new">{E(label)}</span>')
    if it.get("exploration"):
        badges.append('<span class="badge b-exp">탐색 표본</span>')
    badges.append(f'<span class="badge">{BASIS.get(it.get("basis"), "")}</span>')
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
    return (f'<article class="card" id="i-{it["id"]}" data-region="{E(reg)}" style="--rc:{col}"><h4>{E(it["title_ko"])}</h4>'
            f'<div class="meta"><span class="rchip"><span class="sw" style="background:{col}"></span>{E(reg)}</span>{cty_s} · {E(it["publisher"])}{authors} · '
            f'{E((it.get("published") or "")[:10])} {"".join(badges)}</div>'
            f'<p>{E(it["brief"])}</p>{why}<div class="meta">{tags}</div>'
            f'<div class="links"><a href="{E(it.get("resolved_url") or it["url"])}" target="_blank" rel="noopener">원문: {E(it["title"][:90])}</a>'
            f'<a class="pend" href="{E(issue_link(it, date))}" target="_blank" rel="noopener">＋ 심층 대기에 추가</a></div>{also}</article>')


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
    return (f'<div class="mapcard"><div class="map"><img src="{root}assets/world.svg" alt="권역별로 색을 칠한 세계지도. 원의 크기는 오늘 게재된 기사 수"> '
            f'<svg class="overlay" viewBox="0 0 {w["W"]} {w["H"]}">{"".join(bubs)}</svg></div>'
            f'<div class="chips">{chips}</div><div class="selinfo" id="selinfo"></div>'
            f'<div class="ops" style="margin:2px">원 크기 = 오늘 게재 수 · 점선 원 = 오늘 0건 · 회색 국가 = 아직 관찰 범위 밖 · 글로벌 = 논문·국제 행사 등 특정 국가 없는 자료</div></div>')


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
    s = rep["stats"]
    out = [f'<div class="dateline">{E(date_label(date, rep.get("generated_kst")))}</div>'
           f'<div class="funnel">후보 {s["candidates"]}건 → 관련 {s["relevant"]}건 → 사건 {s["events"]}건 → 게재 {len(items)}건</div>',
           ]
    ov = rep.get("overview") or {}
    flows = ov.get("flows") or []
    flows_html = "".join(
        f'<div class="flow"><b>{E(f.get("title", ""))}</b>{E(f.get("text", ""))}<div class="refs">'
        + "".join(f'<a href="#i-{E(i)}">근거 {n + 1}</a>' for n, i in enumerate(f.get("ids", []))) + "</div></div>" for f in flows) \
        or '<p class="ops">오늘은 여러 시장을 가로지르는 뚜렷한 흐름이 없습니다.</p>'
    out.append(f'<div class="hero">{map_block(items, root)}<div class="side"><div class="box"><h4>오늘의 3가지</h4><ol>'
               + "".join(f"<li>{E(t)}</li>" for t in ov.get("top3", []))
               + f'</ol></div><div class="box"><h4>흐름</h4>{flows_html}</div></div></div>')
    secs = [(k, v) for k, v in config.AREAS.items()] + [("novel", "처음 보는 것"), ("gaps", "범위·운영")]
    out.append('<nav class="sec">' + "".join(f'<a href="#s-{k}">{E(v)}</a>' for k, v in secs) + "</nav>")
    out.append('<input id="q" class="filter" placeholder="오늘 리포트 안에서 검색 (국가, 회사, 태그…)">')
    for key, label in config.AREAS.items():
        group = [it for it in items if it["area"] == key]
        out.append(f'<section id="s-{key}" data-area="{key}"><h2>{E(label)} <span class="ops cnt">{len(group)}건</span></h2>'
                   f'<p class="empty"{" style=display:none" if group else ""}>이 조건에 해당하는 기사가 없습니다.</p>')
        out.append('<div class="grid">')
        group.sort(key=lambda it: REGIONS.index(region_of(it)))   # 권역 순으로 이어 붙여 행을 끊지 않는다
        out.append("".join(card(it, date) for it in group))
        out.append("</div></section>")
    novel = [it for it in items if it.get("novel")]
    out.append(f'<section id="s-novel"><h2>처음 보는 것 <span class="ops">{len(novel)}건</span></h2>'
               '<p class="ops">아카이브에 처음 등장한 제품·회사·소재·주제입니다. 위 분야별 목록에도 함께 실려 있습니다.</p>'
               + ("".join(f'<div><a href="#i-{it["id"]}">{E(it["title_ko"])}</a> <span class="ops">({E(region_of(it))} · '
                          f'{E(", ".join(it.get("novel_entities", []) or [it.get("new_topic") or ""]))})</span></div>' for it in novel)
                  or '<p class="ops">기준 기록이 쌓이는 중입니다.</p>') + "</section>")
    fails = [x for x in rep["sources"] if not x["ok"]]
    zero = [x for x in rep["sources"] if x["ok"] and x["n"] == 0]
    out.append('<section id="s-gaps"><h2>범위·운영</h2><p class="ops">권역×분야별 게재 수. 0은 조사한 출처 범위 안에서 오늘 게재할 자료가 없었다는 뜻입니다.</p>'
               + coverage_table(items))
    out.append(f'<p class="ops">출처 {len(rep["sources"])}개 중 접근 실패 {len(fails)}개, 결과 0건 {len(zero)}개.</p>')
    if fails:
        out.append("<details><summary>접근 실패 출처</summary><ul class='ops'>" + "".join(f"<li>{E(x['source'])}: {E(x.get('error', ''))}</li>" for x in fails) + "</ul></details>")
    if zero:
        out.append("<details><summary>결과 0건 출처</summary><ul class='ops'>" + "".join(f"<li>{E(x['source'])}</li>" for x in zero) + "</ul></details>")
    ns = rep.get("not_shown", [])
    if ns:
        out.append(f"<details><summary>관련 판정됐지만 상한 때문에 싣지 않은 사건 {len(ns)}건</summary><ul class='ops'>"
                   + "".join(f'<li><a href="{E(x["url"])}" target="_blank" rel="noopener">{E(x.get("ko") or x["title"])}</a> ({E(x.get("story_country") or x.get("country") or "")})</li>' for x in ns)
                   + "</ul></details>")
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
            "counts": {k: sum(1 for i in latest["items"] if i["area"] == k) for k in config.AREAS},
            "regions": {r: sum(1 for i in latest["items"] if region_of(i) == r) for r in REGIONS},
            "total": len(latest["items"]), "novel": sum(1 for i in latest["items"] if i.get("novel")),
            "usd": latest.get("usage", {}).get("total_usd"),
        }, ensure_ascii=False, indent=1))
    else:
        write("docs/index.html", page(TITLE, "<p>아직 리포트가 없습니다.</p>"))

    # 아카이브 + 전체 검색 (경제 사이트와 같은 날짜 표기 + 그날 헤드라인)
    index = [{"d": r["date"], "id": i["id"], "t": i["title_ko"], "b": i["brief"][:160], "c": country_of(i), "r": region_of(i),
              "a": i["area"], "tg": i.get("tags") or []} for r in reps for i in r["items"]]
    write("docs/search-index.json", json.dumps(index, ensure_ascii=False))
    lst = "".join(f'<li><a href="reports/{r["date"]}.html"><span class="d">{E(date_label(r["date"], r.get("generated_kst")))}</span>'
                  f'<span class="h">{E(headline(r))}</span></a><span class="ops">게재 {len(r["items"])}건</span></li>' for r in reps)
    colors = json.dumps(config.REGION_COLORS, ensure_ascii=False)
    js = """<script>
const RC=""" + colors + """;
fetch('search-index.json').then(r=>r.json()).then(ix=>{const q=document.getElementById('aq'),o=document.getElementById('ares');
const A={car:'자동차',mobility:'모빌리티',research:'리서치',event:'이벤트'};const esc=s=>String(s).replace(/</g,'&lt;');
q.addEventListener('input',()=>{const v=q.value.trim().toLowerCase();if(v.length<2){o.innerHTML='';return}
const hit=ix.filter(x=>(x.t+' '+x.b+' '+x.c+' '+x.r+' '+x.tg.join(' ')).toLowerCase().includes(v)).slice(0,200);
o.innerHTML='<p class=ops>'+hit.length+'건</p>'+hit.map(x=>`<div class=card style="--rc:${RC[x.r]||'#4B515C'}"><h4><a href="reports/${x.d}.html#i-${x.id}">${esc(x.t)}</a></h4><div class=meta>${x.d} · ${esc(x.r)} · ${esc(x.c)} · ${A[x.a]||x.a}</div><p>${esc(x.b)}…</p></div>`).join('')})});
</script>"""
    write("docs/archive.html", page(f"{TITLE} — 아카이브", f'<h2>아카이브·검색</h2><input id="aq" class="filter" placeholder="전체 기간 검색 (2글자 이상: 국가, 권역, 회사, 태그…)"><div id="ares"></div>'
                                   f'<h2>지난 리포트</h2><ul class="arch">{lst}</ul>{js}', script=False))

    # 심층 대기 목록 (GitHub Issues, label=deep-dive)
    pend = []
    if os.path.exists("data/pending.json"):
        with open("data/pending.json", encoding="utf-8") as f:
            pend = json.load(f)
    rows = "".join(f'<div class="card"><h4><a href="{E(p["html_url"])}" target="_blank" rel="noopener">{E(p["title"])}</a></h4>'
                   f'<div class="meta">추가 {E(p["created_at"][:10])} · #{p["number"]}</div></div>' for p in pend)
    write("docs/pending.html", page(f"{TITLE} — 심층 대기 목록",
          f'<h2>심층 대기 목록 <span class="ops">{len(pend)}건</span></h2>'
          f'<p class="ops">리포트의 "＋ 심층 대기에 추가"로 만든 GitHub 이슈 목록입니다. 이 목록은 수집 범위나 점수에 영향을 주지 않습니다. '
          f'심층 조사가 끝난 이슈를 닫으면 목록에서 빠집니다. <a href="https://github.com/{repo()}/issues?q=is%3Aopen+label%3A{config.PENDING_LABEL}" target="_blank">GitHub에서 보기</a></p>'
          + (rows or '<p class="ops">대기 중인 항목이 없습니다.</p>'), script=False))


def fetch_pending():
    """Actions에서 GITHUB_TOKEN으로 열린 deep-dive 이슈를 읽어 data/pending.json에 저장."""
    import requests
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return
    try:
        r = requests.get(f"https://api.github.com/repos/{repo()}/issues",
                         params={"labels": config.PENDING_LABEL, "state": "open", "per_page": 100},
                         headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}, timeout=20)
        r.raise_for_status()
        keep = [{k: i[k] for k in ("number", "title", "html_url", "created_at", "body")} for i in r.json() if "pull_request" not in i]
        write("data/pending.json", json.dumps(keep, ensure_ascii=False, indent=1))
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] pending issues: {e}")


if __name__ == "__main__":
    build_site()
