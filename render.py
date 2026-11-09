"""정적 사이트 생성: data/reports/*.json → docs/ (GitHub Pages)."""
import glob
import html
import json
import os
import urllib.parse

import config

E = html.escape

CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6a66;--line:#e4e1da;--card:#fff;--acc:#2a5bd7;--new:#b3261e;--exp:#7a4dbf;--chip:#f1efe9}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--fg:#ecebe6;--mut:#a3a19a;--line:#2e2d2a;--card:#1c1c1a;--acc:#7ea2ff;--new:#ff8a80;--exp:#c3a6ff;--chip:#262522}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.7 "Pretendard","Apple SD Gothic Neo","Noto Sans KR",system-ui,sans-serif}
a{color:var(--acc)}.wrap{max-width:980px;margin:0 auto;padding:24px 20px 80px}
header.top{border-bottom:2px solid var(--fg);padding-bottom:14px;margin-bottom:8px}
header.top h1{font-size:28px;margin:0;letter-spacing:-.5px}header.top .sub{color:var(--mut);font-size:14px}
nav.main{display:flex;gap:14px;flex-wrap:wrap;font-size:14px;margin:10px 0 0}
nav.sec{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:8px 0;z-index:5;display:flex;gap:8px;flex-wrap:wrap}
nav.sec{scrollbar-width:none}@media(max-width:640px){nav.sec{flex-wrap:nowrap;overflow-x:auto}nav.sec a{white-space:nowrap}}
section,.card{scroll-margin-top:56px}
nav.sec a{font-size:13px;text-decoration:none;padding:3px 10px;border:1px solid var(--line);border-radius:99px;color:var(--fg)}
h2{font-size:22px;margin:36px 0 10px;border-top:1px solid var(--fg);padding-top:14px}h3{font-size:15px;color:var(--mut);margin:22px 0 8px;font-weight:600}
.top3 ol{padding-left:20px;font-size:17px}.flow{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:10px 0}
.flow b{display:block;margin-bottom:4px}.flow .refs a{font-size:12px;margin-right:6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:10px 0}
.card h4{margin:0 0 4px;font-size:17px;line-height:1.45}.meta{font-size:12.5px;color:var(--mut);display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.chip{background:var(--chip);border-radius:4px;padding:0 6px;font-size:12px;color:var(--fg);cursor:pointer}
.badge{border-radius:4px;padding:0 6px;font-size:11.5px;font-weight:700;border:1px solid currentColor}
.b-new{color:var(--new)}.b-exp{color:var(--exp)}.b-basis{color:var(--mut)}
.card p{margin:8px 0}.why{font-size:14.5px;border-left:3px solid var(--acc);padding-left:10px;color:var(--fg)}
.links{font-size:13px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}.also{font-size:12.5px;color:var(--mut)}
.pend{font-size:12.5px;text-decoration:none;border:1px solid var(--acc);border-radius:6px;padding:2px 10px}
.filter{width:100%;padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font-size:15px;margin:14px 0 4px}
table.cov{border-collapse:collapse;font-size:13px;width:100%}table.cov td,table.cov th{border:1px solid var(--line);padding:4px 8px;text-align:center}
table.cov td.zero{color:var(--new);font-weight:700}table.cov th:first-child,table.cov td:first-child{text-align:left}
.ops{font-size:13px;color:var(--mut)}details summary{cursor:pointer}footer{margin-top:50px;font-size:12.5px;color:var(--mut);border-top:1px solid var(--line);padding-top:12px}
.arch li{margin:6px 0}
"""

FILTER_JS = """
<script>
(function(){const q=document.getElementById('q');if(!q)return;const cards=[...document.querySelectorAll('.card')];
function f(){const v=q.value.trim().toLowerCase();cards.forEach(c=>{c.style.display=!v||c.innerText.toLowerCase().includes(v)?'':'none'})}
q.addEventListener('input',f);document.querySelectorAll('.chip').forEach(ch=>ch.addEventListener('click',()=>{q.value=ch.textContent;f();q.scrollIntoView({behavior:'smooth'})}));})();
</script>"""


def repo():
    return os.environ.get("GITHUB_REPOSITORY") or config.DEFAULT_REPO


def pages_base():
    owner, name = repo().split("/", 1)
    return f"https://{owner.lower()}.github.io/{name}/"


def page(title, body, root=""):
    nav = (f'<nav class="main"><a href="{root}index.html">오늘의 리포트</a><a href="{root}archive.html">아카이브·검색</a>'
           f'<a href="{root}pending.html">심층 대기 목록</a></nav>')
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(title)}</title><style>{CSS}</style></head><body><div class="wrap">'
            f'<header class="top"><h1>2027 Mobility Updates</h1><div class="sub">전 세계 자동차·모빌리티 소식, 매일 아침 한국어로</div>{nav}</header>'
            f'{body}<footer>모든 단신은 원문을 재구성한 요약이며 원문 링크를 함께 제공합니다. 투자 판단의 근거가 아닙니다.</footer></div>{FILTER_JS}</body></html>')


def issue_link(it, date):
    body = (f"id: {it['id']}\n리포트: {date}\n원문: {it.get('resolved_url') or it['url']}\n"
            f"국가: {it['country']} / 매체: {it['publisher']}\n분야: {config.AREAS.get(it['area'], it['area'])}\n\n"
            f"단신:\n{it['brief']}\n\n심층 조사에서 보고 싶은 점(선택):\n")
    q = urllib.parse.urlencode({"labels": config.PENDING_LABEL, "title": f"[심층] {it['title_ko']}", "body": body})
    return f"https://github.com/{repo()}/issues/new?{q}"


BASIS = {"body": "본문 기반", "snippet": "헤드라인·요약 기반", "abstract": "초록 기반"}


def card(it, date):
    badges = []
    if it.get("novel"):
        label = "처음 보는 것" + (": " + ", ".join(it.get("novel_entities", [])[:2]) if it.get("novel_entities") else "")
        badges.append(f'<span class="badge b-new">{E(label)}</span>')
    if it.get("exploration"):
        badges.append('<span class="badge b-exp">탐색 표본</span>')
    badges.append(f'<span class="badge b-basis">{BASIS.get(it.get("basis"), "")}</span>')
    tags = "".join(f'<span class="chip">{E(t)}</span>' for t in (it.get("tags") or []))
    if it.get("new_topic"):
        tags += f'<span class="chip">새 주제: {E(it["new_topic"])}</span>'
    date_s = (it.get("published") or "")[:10]
    countries = it.get("countries") or [it["country"]]
    also = ""
    if it.get("also"):
        also = '<div class="also">같은 사건 다른 보도: ' + ", ".join(
            f'<a href="{E(a["url"])}" rel="noopener" target="_blank">{E(a["publisher"])}({E(a["country"])})</a>' for a in it["also"]) + "</div>"
    why = f'<p class="why">{E(it["why"])}</p>' if it.get("why") else ""
    authors = f' · {E(it["authors"])}' if it.get("authors") else ""
    return (f'<article class="card" id="i-{it["id"]}"><h4>{E(it["title_ko"])}</h4>'
            f'<div class="meta">{E(" · ".join(countries))} · {E(it["publisher"])}{authors} · {E(date_s)} {"".join(badges)}</div>'
            f'<p>{E(it["brief"])}</p>{why}<div class="meta">{tags}</div>'
            f'<div class="links"><a href="{E(it.get("resolved_url") or it["url"])}" target="_blank" rel="noopener">원문: {E(it["title"][:90])}</a>'
            f'<a class="pend" href="{E(issue_link(it, date))}" target="_blank" rel="noopener">＋ 심층 대기에 추가</a></div>{also}</article>')


def coverage_table(rep):
    regions = list(config.REGIONS) + ["글로벌"]
    cnt = {(r, a): 0 for r in regions for a in config.AREAS}
    for it in rep["items"]:
        key = (it["region"], it["area"])
        if key in cnt:
            cnt[key] += 1
    head = "".join(f"<th>{E(v)}</th>" for v in config.AREAS.values())
    rows = ""
    for r in regions:
        cells = "".join(f'<td class="{"zero" if cnt[(r, a)] == 0 else ""}">{cnt[(r, a)]}</td>' for a in config.AREAS)
        rows += f"<tr><td>{E(r)}</td>{cells}</tr>"
    return f'<table class="cov"><tr><th>권역</th>{head}</tr>{rows}</table>'


def report_body(rep, root=""):
    date, items = rep["date"], rep["items"]
    s = rep["stats"]
    out = [f'<p class="sub">{E(date)} · 기준 {E(rep["generated_kst"])} KST · 후보 {s["candidates"]}건 → 관련 {s["relevant"]}건 → 사건 {s["events"]}건 → 게재 {len(items)}건</p>']
    secs = [("top", "오늘의 3가지"), ("flows", "흐름")] + [(k, v) for k, v in config.AREAS.items()] + [("novel", "처음 보는 것"), ("gaps", "공백·범위")]
    out.append('<nav class="sec">' + "".join(f'<a href="#s-{k}">{E(v)}</a>' for k, v in secs) + "</nav>")
    out.append('<input id="q" class="filter" placeholder="오늘 리포트 안에서 검색 (국가, 회사, 태그…)">')
    ov = rep.get("overview") or {}
    out.append('<section id="s-top" class="top3"><h2>오늘의 3가지</h2><ol>' + "".join(f"<li>{E(t)}</li>" for t in ov.get("top3", [])) + "</ol></section>")
    flows = ov.get("flows") or []
    out.append('<section id="s-flows"><h2>흐름</h2>' + ("".join(
        f'<div class="flow"><b>{E(f.get("title", ""))}</b>{E(f.get("text", ""))}<div class="refs">'
        + "".join(f'<a href="#i-{E(i)}">근거 {n + 1}</a>' for n, i in enumerate(f.get("ids", []))) + "</div></div>" for f in flows)
        or '<p class="ops">오늘은 여러 시장을 가로지르는 뚜렷한 흐름이 없습니다.</p>') + "</section>")
    for key, label in config.AREAS.items():
        group = [it for it in items if it["area"] == key]
        out.append(f'<section id="s-{key}"><h2>{E(label)} <span class="ops">{len(group)}건</span></h2>')
        if not group:
            out.append('<p class="ops">오늘 이 분야에 게재할 신호가 없습니다.</p>')
        for region in list(config.REGIONS) + ["글로벌"]:
            rg = [it for it in group if it["region"] == region]
            if rg:
                out.append(f"<h3>{E(region)}</h3>" + "".join(card(it, date) for it in rg))
        out.append("</section>")
    novel = [it for it in items if it.get("novel")]
    out.append(f'<section id="s-novel"><h2>처음 보는 것 <span class="ops">{len(novel)}건</span></h2><p class="ops">아카이브에 처음 등장한 제품·회사·소재·주제입니다. 위 분야별 목록에도 함께 실려 있습니다.</p>'
               + "".join(f'<div><a href="#i-{it["id"]}">{E(it["title_ko"])}</a> <span class="ops">({E(it["country"])} · {E(", ".join(it.get("novel_entities", []) or [it.get("new_topic") or ""]))})</span></div>' for it in novel)
               + "</section>")
    fails = [x for x in rep["sources"] if not x["ok"]]
    zero = [x for x in rep["sources"] if x["ok"] and x["n"] == 0]
    out.append('<section id="s-gaps"><h2>공백·범위</h2><p class="ops">권역×분야별 게재 수. 0은 오늘 해당 칸에서 게재된 자료가 없다는 뜻이며, 조사한 출처 범위 안에서만 성립합니다.</p>'
               + coverage_table(rep))
    out.append(f'<p class="ops">출처 {len(rep["sources"])}개 중 접근 실패 {len(fails)}개, 결과 0건 {len(zero)}개.</p>')
    if fails:
        out.append("<details><summary>접근 실패 출처</summary><ul class='ops'>" + "".join(f"<li>{E(x['source'])}: {E(x.get('error', ''))}</li>" for x in fails) + "</ul></details>")
    if zero:
        out.append("<details><summary>결과 0건 출처</summary><ul class='ops'>" + "".join(f"<li>{E(x['source'])}</li>" for x in zero) + "</ul></details>")
    ns = rep.get("not_shown", [])
    if ns:
        out.append(f"<details><summary>관련 판정됐지만 상한 때문에 싣지 않은 사건 {len(ns)}건</summary><ul class='ops'>"
                   + "".join(f'<li><a href="{E(x["url"])}" target="_blank" rel="noopener">{E(x.get("ko") or x["title"])}</a> ({E(x["country"])})</li>' for x in ns) + "</ul></details>")
    held = rep.get("held", 0)
    c = rep.get("usage", {})
    out.append(f'<p class="ops">운영: Claude 실측 비용 ${c.get("total_usd", 0):.4f} (상한 ${c.get("budget_usd", 0)}) · 가격 기준일 {config.PRICES_CHECKED}'
               + (f" · 예산 초과로 보류 {held}건" if held else "") + "</p></section>")
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


def build_site():
    reps = load_reports()
    os.makedirs("docs/reports", exist_ok=True)
    write("docs/.nojekyll", "")
    for r in reps:
        write(f"docs/reports/{r['date']}.html", page(f"2027 Mobility Updates {r['date']}", report_body(r, "../"), "../"))
    if reps:
        write("docs/index.html", page(f"2027 Mobility Updates {reps[0]['date']}", report_body(reps[0])))
        latest = reps[0]
        write("docs/latest.json", json.dumps({
            "date": latest["date"], "generated_kst": latest["generated_kst"],
            "url": pages_base() + f"reports/{latest['date']}.html", "home": pages_base(),
            "top3": (latest.get("overview") or {}).get("top3", []),
            "counts": {k: sum(1 for i in latest["items"] if i["area"] == k) for k in config.AREAS},
            "total": len(latest["items"]), "novel": sum(1 for i in latest["items"] if i.get("novel")),
            "usd": latest.get("usage", {}).get("total_usd"),
        }, ensure_ascii=False, indent=1))
    else:
        write("docs/index.html", page("2027 Mobility Updates", "<p>아직 리포트가 없습니다.</p>"))

    # 아카이브 + 전체 검색
    index = [{"d": r["date"], "id": i["id"], "t": i["title_ko"], "b": i["brief"][:160], "c": i["country"], "a": i["area"],
              "tg": i.get("tags") or []} for r in reps for i in r["items"]]
    write("docs/search-index.json", json.dumps(index, ensure_ascii=False))
    lst = "".join(f'<li><a href="reports/{r["date"]}.html">{r["date"]}</a> · {len(r["items"])}건 · '
                  f'{E(((r.get("overview") or {}).get("top3") or [""])[0])}</li>' for r in reps)
    js = """<script>
fetch('search-index.json').then(r=>r.json()).then(ix=>{const q=document.getElementById('aq'),o=document.getElementById('ares');
const A={car:'자동차',mobility:'모빌리티',research:'리서치',event:'이벤트'};
q.addEventListener('input',()=>{const v=q.value.trim().toLowerCase();if(v.length<2){o.innerHTML='';return}
const hit=ix.filter(x=>(x.t+' '+x.b+' '+x.c+' '+x.tg.join(' ')).toLowerCase().includes(v)).slice(0,200);
o.innerHTML='<p class=ops>'+hit.length+'건</p>'+hit.map(x=>`<div class=card><h4><a href="reports/${x.d}.html#i-${x.id}">${x.t.replace(/</g,'&lt;')}</a></h4><div class=meta>${x.d} · ${x.c} · ${A[x.a]||x.a}</div><p>${x.b.replace(/</g,'&lt;')}…</p></div>`).join('')})});
</script>"""
    write("docs/archive.html", page("아카이브·검색", f'<h2>아카이브·검색</h2><input id="aq" class="filter" placeholder="전체 기간 검색 (2글자 이상)"><div id="ares"></div>'
                                   f'<h2>지난 리포트</h2><ul class="arch">{lst}</ul>{js}'))

    # 심층 대기 목록 (GitHub Issues, label=deep-dive)
    pend = []
    if os.path.exists("data/pending.json"):
        with open("data/pending.json", encoding="utf-8") as f:
            pend = json.load(f)
    rows = "".join(f'<div class="card"><h4><a href="{E(p["html_url"])}" target="_blank" rel="noopener">{E(p["title"])}</a></h4>'
                   f'<div class="meta">추가 {E(p["created_at"][:10])} · #{p["number"]}</div></div>' for p in pend)
    write("docs/pending.html", page("심층 대기 목록",
          f'<h2>심층 대기 목록 <span class="ops">{len(pend)}건</span></h2>'
          f'<p class="ops">리포트의 "＋ 심층 대기에 추가"로 만든 GitHub 이슈 목록입니다(다음 실행 때 갱신). 이 목록은 수집 범위나 점수에 영향을 주지 않습니다. '
          f'심층 조사가 끝난 이슈를 닫으면 목록에서 빠집니다. <a href="https://github.com/{repo()}/issues?q=is%3Aopen+label%3A{config.PENDING_LABEL}" target="_blank">GitHub에서 보기</a></p>'
          + (rows or "<p>대기 중인 항목이 없습니다.</p>")))


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
