"""2~5단계: 분류(저비용) → 커버리지 기반 선정(토큰 0) → 본문 확보(토큰 0) → 단신(저비용) → 오늘의 흐름.

원칙: 사용자의 심층 선택은 여기 어떤 점수에도 쓰이지 않는다. 선정 기준은 커버리지·새로움·탐색 표본.
"""
import json
import os
import random
import urllib.parse
from collections import defaultdict

import requests

import config
from llm import BudgetExceeded

TRIAGE_SYSTEM = f"""너는 자동차·모빌리티 디자이너와 기획자를 위한 글로벌 관찰 데스크의 1차 분류 담당이다.
입력은 여러 나라·언어의 기사/논문 제목 목록이다. 관련 있는 항목만 JSON 배열로 출력한다. 관련 없는 항목은 출력하지 않는다.

관련 있음: 차량·이동수단의 제품, 출시 사양·가격, 사용자와 사용 조건, 디자인(외장·실내·HMI·CMF·패키징), 기술, 제조·소재,
서비스·인프라, 연구, 전시·행사. 자동차와 무관한 일반 AI·건축·스마트팜, 해외 주재원 이동(global mobility), 단순 사건사고, 스포츠, 주가만 다룬 기사는 제외.

필드:
- id: 입력 id 그대로
- area: car | mobility | research | event
- tags: 다음 중 최대 3개 {json.dumps(config.TAGS, ensure_ascii=False)}
- new_topic: 목록에 없는 새 주제면 짧은 한국어 이름, 아니면 null
- entities: 제품·회사·소재·기관 고유명사 최대 4개 (원어 표기)
- event: 같은 사건을 묶기 위한 짧은 영어 slug (예: "byd-atto2-indonesia-launch")
- score: 1~5. 디자인·기획 실무자에게 새 정보인 정도. 회사 규모·영어 여부·유명세로 점수를 올리지 마라.
  소외 시장의 현지 제품·사용 조건, 처음 보는 접근은 높게 준다.
- ko: 한국어 제목. 일본어·중국어·영어 등 어떤 언어든 반드시 한국어로 번역한다 (원문 의미 그대로, 과장 금지)
- story_country: 기사가 다루는 나라(한국어 이름, 예: 중국, 인도네시아). 수집 경로(입력의 국가 칸)가 아니라 기사 내용 기준.
  여러 나라·국제 행사·논문처럼 특정 국가가 없으면 "글로벌"
- story_region: story_country가 속한 권역. 북미(미국·캐나다·멕시코) / 유럽(러시아 포함) / 동아시아(중·일·한·대만·몽골) /
  남아시아 / 동남아시아 / 서남아시아(튀르키예·중동·이란) / 아프리카 / 글로벌. 중남미·오세아니아 등 그 밖이면 "글로벌"

output 도구의 items로 제출한다."""

BRIEF_SYSTEM = """너는 자동차·모빌리티 디자이너·기획자용 데일리 리포트의 단신 기자다. 각 항목에 대해 한국어 단신을 쓴다.

규칙:
- 첫 문장에 누가·언제·어디서·무엇을 했는지 드러낸다. 전체 2~4문장, 완전한 문장.
- 주장의 주체를 남긴다: "제조사는 …라고 밝혔다", "연구진은 …를 보고했다", "현지 매체는 …라고 보도했다".
- 주어진 텍스트에 있는 사실만 쓴다. 숫자·가격·사양은 단위·시장·조건과 함께. 추측·과장·투자 권유 금지.
- 원문 문장을 옮겨 적지 말고 재구성한다. 인용은 꼭 필요할 때 짧게 한 번만.
- why: 디자인·기획 의사결정에 닿는 구체적 지점(예: 수납 배치, 조작계, 소재 내구성, 현지 사용 조건)을 한 문장. 텍스트로 뒷받침되지 않으면 빈 문자열.
- 텍스트에 없는 내용은 언급하지 말고 그냥 쓰지 않는다. "본문에 포함되지 않았다", "제목 수준", "확인되지 않았다",
  "구체적 내용은 전해지지 않았다" 같은 자료 한계·작업 과정 문장을 절대 쓰지 않는다. 근거 수준은 화면에 따로 표시된다.
  텍스트가 짧으면 1~2문장으로 짧게 끝낸다.

output 도구의 items로 제출한다."""

OVERVIEW_SYSTEM = """너는 글로벌 모빌리티 관찰 데스크의 편집장이다. 오늘 실린 단신 목록을 보고:
- top3: 오늘 가장 눈여겨볼 3가지를 각각 한 문장(한국어). 시장·제품·연구를 섞어서, 큰 회사 편향을 피한다.
- flows: 여러 시장·기사를 가로지르는 흐름 2~4개. 각 {"title": 내용이 드러나는 제목, "text": 2~3문장, "ids": 근거 단신 id 목록}.
  단신에 없는 사실을 만들지 않는다. 연결이 약하면 flows를 줄인다.
output 도구로 제출한다."""


S = {"type": "string"}
TRIAGE_SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {"type": "array", "items": {
    "type": "object", "required": ["id", "area", "score", "ko"],
    "properties": {"id": S, "area": {"type": "string", "enum": list(config.AREAS)}, "tags": {"type": "array", "items": S},
                   "new_topic": {"type": ["string", "null"]}, "entities": {"type": "array", "items": S},
                   "event": S, "score": {"type": "integer"}, "ko": S, "story_country": S,
                   "story_region": {"type": "string", "enum": list(config.REGION_COLORS)}}}}}}
BRIEF_SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {"type": "array", "items": {
    "type": "object", "required": ["id", "title_ko", "brief"],
    "properties": {"id": S, "title_ko": S, "brief": S, "why": S}}}}}
OVERVIEW_SCHEMA = {"type": "object", "required": ["top3", "flows"], "properties": {
    "top3": {"type": "array", "items": S},
    "flows": {"type": "array", "items": {"type": "object", "properties": {"title": S, "text": S, "ids": {"type": "array", "items": S}}}}}}


def triage(llm, items):
    out, held = {}, []
    for i in range(0, len(items), config.TRIAGE_BATCH):
        batch = items[i:i + config.TRIAGE_BATCH]
        lines = [f'{it["id"]} | {it["country"]} | {it["publisher"]} | {it["title"]} | {it["snippet"][:120]}' for it in batch]
        try:
            res = llm.json_call(model=config.CHEAP_MODEL, system=TRIAGE_SYSTEM, user="\n".join(lines),
                                max_tokens=8000, stage="triage", schema=TRIAGE_SCHEMA).get("items", [])
        except BudgetExceeded:
            held += items[i:]
            break
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] triage batch {i}: {e}")
            continue
        for r in res if isinstance(res, list) else []:
            if r.get("id"):
                out[r["id"]] = r
    return out, held


def select(items, tri, known_entities, seed):
    kept = []
    for it in items:
        t = tri.get(it["id"])
        if not t:
            continue
        it.update({k: t.get(k) for k in ("area", "tags", "new_topic", "entities", "event", "score", "ko", "story_country", "story_region")})
        if it.get("story_region") not in config.REGION_COLORS:
            it["story_region"] = it["region"] if it["region"] in config.REGION_COLORS else "글로벌"
        if it["area"] not in config.AREAS:
            it["area"] = "research" if it["kind"] == "paper" else "car"
        ents = [e for e in (it.get("entities") or []) if isinstance(e, str)]
        # 첫 실행(기록 없음)에는 전부가 '처음'이 되므로 고유명사 기준 새로움을 끈다
        it["novel_entities"] = [e for e in ents if e.lower() not in known_entities] if known_entities else []
        it["novel"] = bool(it["novel_entities"] or it.get("new_topic"))
        it["rank"] = float(it.get("score") or 1) + (1.5 if it["novel"] else 0)
        kept.append(it)

    # 같은 사건 묶기: 대표 1건(직접 RSS > 현지 매체 > 기타) + 다른 보도 목록
    groups = defaultdict(list)
    for it in kept:
        groups[it.get("event") or it["id"]].append(it)
    reps = []
    for g in groups.values():
        g.sort(key=lambda x: (x["kind"] != "rss", -x["rank"]))
        rep = g[0]
        rep["also"] = [{"publisher": o["publisher"], "url": o["url"], "country": o["country"]} for o in g[1:]][:8]
        rep["countries"] = sorted({o.get("story_country") or o["country"] for o in g})
        reps.append(rep)

    reps.sort(key=lambda x: -x["rank"])
    chosen, ids = [], set()

    def take(it):
        if it["id"] not in ids and len(chosen) < config.MAX_BRIEFS - config.EXPLORATION_SLOTS:
            chosen.append(it)
            ids.add(it["id"])

    for key, minimum in (("story_region", config.MIN_PER_REGION), ("area", config.MIN_PER_AREA)):
        by = defaultdict(list)
        for it in reps:
            by[it[key]].append(it)
        for lst in by.values():
            for it in lst[:minimum]:
                take(it)
    for it in reps:
        take(it)

    rest = [it for it in reps if it["id"] not in ids]
    rng = random.Random(seed)
    for it in rng.sample(rest, min(config.EXPLORATION_SLOTS, len(rest))):
        it["exploration"] = True
        chosen.append(it)
        ids.add(it["id"])
    not_shown = [it for it in reps if it["id"] not in ids]
    return chosen, not_shown, len(kept), len(reps)


def get_body(it):
    """본문 확보(토큰 0). Google News 중계 링크가 원문으로 풀리지 않으면 제목·요약 기반으로 남긴다."""
    if it["kind"] == "paper":
        return it.get("snippet", ""), "abstract"
    try:
        import trafilatura
        r = requests.get(it["url"], headers={"User-Agent": "Mozilla/5.0 2027MobilityUpdates"}, timeout=10, allow_redirects=True)
        host = urllib.parse.urlsplit(r.url).netloc
        if "news.google.com" in host or r.status_code >= 400:
            return it.get("snippet", ""), "snippet"
        it["resolved_url"] = r.url
        text = trafilatura.extract(r.text, include_comments=False, include_tables=False) or ""
        if len(text) > 300:
            return text[: config.BODY_CHARS], "body"
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] body {it['url'][:80]}: {e}")
    return it.get("snippet", ""), "snippet"


def write_briefs(llm, chosen):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=16) as ex:
        for it, (text, basis) in zip(chosen, ex.map(get_body, chosen)):
            it["text"], it["basis"] = text, basis
    print(f"[INFO] 본문 확보: body {sum(1 for x in chosen if x['basis']=='body')} / {len(chosen)}")
    done, held = [], []
    for i in range(0, len(chosen), config.BRIEF_BATCH):
        batch = chosen[i:i + config.BRIEF_BATCH]
        payload = [{"id": it["id"], "country": it.get("story_country") or it["country"], "publisher": it["publisher"], "published": it["published"],
                    "title": it["title"], "authors": it.get("authors", ""), "basis": it["basis"], "text": it["text"]}
                   for it in batch]
        try:
            res = llm.json_call(model=config.CHEAP_MODEL, system=BRIEF_SYSTEM,
                                user=json.dumps(payload, ensure_ascii=False), max_tokens=6000, stage="brief", schema=BRIEF_SCHEMA).get("items", [])
        except BudgetExceeded:
            held += chosen[i:]
            break
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] brief batch {i}: {e}")
            continue
        got = {r["id"]: r for r in res if isinstance(r, dict) and r.get("id")}
        for it in batch:
            r = got.get(it["id"])
            if r and r.get("brief"):
                it["title_ko"] = r.get("title_ko") or it.get("ko") or it["title"]
                it["brief"] = r["brief"]
                it["why"] = r.get("why", "")
                it.pop("text", None)
                done.append(it)
    return done, held


def overview(llm, briefs):
    lines = [{"id": b["id"], "area": b["area"], "country": b.get("story_country") or b["country"], "title": b["title_ko"], "brief": b["brief"][:220]}
             for b in briefs]
    model = config.MID_MODEL if config.USE_MID_MODEL_FOR_OVERVIEW else config.CHEAP_MODEL
    user = json.dumps(lines, ensure_ascii=False)
    res = None
    for m in dict.fromkeys([model, config.CHEAP_MODEL]):
        try:
            res = llm.json_call(model=m, system=OVERVIEW_SYSTEM, user=user,
                                max_tokens=8000, stage="overview", schema=OVERVIEW_SCHEMA)
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] overview({m}): {e}")
            continue
        if res.get("top3") and res.get("flows"):
            return res
        print(f"[WARN] overview({m}): 흐름 누락, 다음 모델로 재시도")
    return {"top3": (res or {}).get("top3") or [b["title_ko"] for b in briefs[:3]], "flows": (res or {}).get("flows") or []}


def load_entities(path="data/entities.json"):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_entities(known, briefs, path="data/entities.json"):
    for b in briefs:
        for e in b.get("entities") or []:
            if isinstance(e, str):
                known.add(e.lower())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(known), f, ensure_ascii=False)
