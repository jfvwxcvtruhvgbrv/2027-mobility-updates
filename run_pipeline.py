"""전체 실행: 수집 → 분류 → 선정 → 단신 → 흐름 → 저장 → 사이트 생성.

실패 처리: 키 없음 / 후보 0건 / 단신 0건이면 저장·배포 없이 종료코드 1 (조용한 실패 방지).
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import config
import fetch
import process
import render
from llm import LLM

KST = timezone(timedelta(hours=9))


def load_seen(path="data/seen.json"):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY 없음")
        sys.exit(1)
    now = datetime.now(timezone.utc)
    date = now.astimezone(KST).date().isoformat()
    os.makedirs("data/reports", exist_ok=True)

    items, sources = fetch.fetch_all(now)
    seen = load_seen()
    fresh = [it for it in items if it["id"] not in seen]
    print(f"[INFO] 후보 {len(items)}건, 새 후보 {len(fresh)}건, 출처 {len(sources)}개")
    if not fresh:
        print("[ERROR] 새 후보 0건")
        sys.exit(1)

    llm = LLM()
    tri, held_tri = process.triage(llm, fresh)
    known = process.load_entities()
    chosen, not_shown, relevant, events = process.select(fresh, tri, known, seed=date)
    briefs, held_brief = process.write_briefs(llm, chosen)
    print(f"[INFO] 관련 {relevant}, 사건 {events}, 단신 {len(briefs)}, 보류 {len(held_tri) + len(held_brief)}")
    if not briefs:
        print("[ERROR] 단신 0건")
        sys.exit(1)
    ov = process.overview(llm, briefs)

    held = held_tri + held_brief
    if held:
        os.makedirs("data/hold", exist_ok=True)
        with open(f"data/hold/{date}.json", "w", encoding="utf-8") as f:
            json.dump(held, f, ensure_ascii=False)

    report = {
        "date": date, "generated_kst": now.astimezone(KST).strftime("%H:%M"),
        "stats": {"candidates": len(fresh), "relevant": relevant, "events": events},
        "overview": ov, "items": briefs, "sources": sources,
        "not_shown": [{k: x.get(k) for k in ("id", "title", "ko", "url", "country", "area")} for x in not_shown],
        "held": len(held), "usage": llm.summary(),
    }
    with open(f"data/reports/{date}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    # 처리 이력: 보류된 후보는 다음 실행에서 다시 보도록 seen에 넣지 않는다
    held_ids = {h["id"] for h in held}
    for it in fresh:
        if it["id"] not in held_ids:
            seen[it["id"]] = date
    cutoff = (now - timedelta(days=60)).astimezone(KST).date().isoformat()
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    with open("data/seen.json", "w", encoding="utf-8") as f:
        json.dump(seen, f)
    process.save_entities(known, briefs + not_shown)

    render.fetch_pending()
    render.build_site()
    print(f"[INFO] 완료 {date}: 게재 {len(briefs)}건, 비용 ${llm.spent:.4f}")


if __name__ == "__main__":
    main()
