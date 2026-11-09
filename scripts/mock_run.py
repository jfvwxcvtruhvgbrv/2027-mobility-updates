"""API 키·네트워크 없이 전체 흐름과 화면을 확인하는 목업 실행.

python scripts/mock_run.py  →  data/, docs/ 에 가짜 리포트 2일치 생성 (실제 데이터 아님)
"""
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ANTHROPIC_API_KEY", "mock")

import config  # noqa: E402
import fetch  # noqa: E402
import llm as llm_mod  # noqa: E402
import process  # noqa: E402
import run_pipeline  # noqa: E402

SAMPLES = [
    ("인도네시아", "동남아시아", "detikOto", "Motor listrik baru dengan bagasi 30 liter", "car", ["이륜차", "패키징"], ["Polytron Fox-S"]),
    ("인도", "남아시아", "Autocar India", "New compact SUV launched with physical climate controls", "car", ["신차·현지출시", "실내·HMI"], ["Tata Nexon"]),
    ("중국", "동아시아", "汽车之家", "新款纯电轿车 发布 智能座舱 取消物理按键", "car", ["실내·HMI", "전동화"], ["Xiaomi SU7"]),
    ("케냐", "아프리카", "Business Daily", "Electric boda boda battery swap network expands", "mobility", ["이륜차", "충전"], ["Roam", "Spiro"]),
    ("독일", "유럽", "electrive", "Cargo bike maker unveils modular rear box", "mobility", ["카고바이크"], ["Urban Arrow"]),
    ("글로벌", "글로벌", "arXiv", "Generative CAD for vehicle interior trim with constraint preservation", "research", ["디자인프로세스·도구", "IT·SW·AI"], ["CAD-GPT"]),
    ("글로벌", "글로벌", "Materials & Design", "Perceived quality of recycled PET textiles in car seats", "research", ["CMF·소재", "PQ(감성품질)"], ["rPET"]),
    ("한국", "동아시아", "글로벌오토뉴스", "서울 모빌리티 전시회 다음 달 개막, 소형 다목적 이동체 대거 출품", "event", ["모터쇼·전시", "농어촌·다목적"], ["서울모빌리티쇼"]),
    ("UAE", "서남아시아", "DriveArabia", "سيارة كهربائية جديدة مع نظام تبريد للمناخ الحار", "car", ["전동화", "실내·HMI"], ["Hongqi E-HS9"]),
    ("미국", "북미", "Electrek", "Robotaxi service adds wheelchair-accessible vans", "mobility", ["자율주행", "교통약자·접근성"], ["Waymo"]),
    ("일본", "동아시아", "Car Watch", "軽EV 新型 発表 荷室高さを拡大", "car", ["신차·현지출시", "패키징"], ["Honda N-VAN e"]),
    ("나이지리아", "아프리카", "Punch", "Locally assembled tricycle EV targets last-mile logistics", "mobility", ["배송·물류", "상용차"], ["Saglev"]),
    ("이탈리아", "유럽", "Auto & Design", "Concept car revives 1970s wedge proportions", "car", ["레트로·클래식", "콘셉트카"], ["Italdesign"]),
    ("미국", "북미", "CES", "CES 2027 announces mobility tech zone expansion", "event", ["모터쇼·전시"], ["CES"]),
]


def fake_items(day):
    out = []
    for n, (country, region, pub, title, *_rest) in enumerate(SAMPLES):
        url = f"https://example.org/{day}/{n}"
        out.append({"id": fetch.uid(url), "url": url, "title": title, "snippet": f"(목업) {title} 요약문.",
                    "publisher": pub, "region": region, "country": country,
                    "published": f"{day}T03:00:00+00:00", "kind": "paper" if region == "글로벌" and n in (5, 6) else "rss"})
    status = [{"source": f"Google News {c[0]}: {c[4][0]}", "region": r, "country": c[0], "ok": True, "n": random.randint(0, 20)}
              for r, cs in config.REGIONS.items() for c in cs]
    status[3]["ok"], status[3]["error"] = False, "HTTP 403 (목업)"
    return out, status


class FakeLLM:
    def __init__(self, *a, **k):
        self.spent, self.budget, self.calls = 0.0, config.RUN_BUDGET_USD, []

    def json_call(self, *, model, system, user, max_tokens, stage):
        self.spent += 0.002
        self.calls.append({"stage": stage, "input": 1000, "output": 200, "usd": 0.002})
        if stage == "triage":
            res = []
            for line in user.splitlines():
                iid, country, pub, title, _ = [x.strip() for x in line.split("|", 4)]
                s = next(x for x in SAMPLES if x[3] == title)
                res.append({"id": iid, "area": s[4], "tags": s[5], "new_topic": None, "entities": s[6],
                            "event": iid, "score": random.randint(2, 5), "ko": "(목업) " + title})
            return res
        if stage == "brief":
            return [{"id": p["id"], "title_ko": f"(목업) {p['country']} {p['publisher']} 기사 제목",
                     "brief": f"{p['publisher']}는 {p['country']} 시장에서 새 제품을 공개했다고 보도했다. 이 문장은 화면 확인용 목업이며 실제 사실이 아니다. 실제 실행에서는 원문 본문을 재구성한 2~4문장이 들어간다.",
                     "why": "수납 위치와 조작계 배치가 현지 사용 조건과 어떻게 맞물리는지 보여주는 사례다." if random.random() > .4 else ""}
                    for p in json.loads(user)]
        ids = [x["id"] for x in json.loads(user)]
        return {"top3": ["(목업) 신흥시장 전동 이륜차의 배터리 교환망 확대", "(목업) 물리 조작계 회귀 사례", "(목업) 재생 소재 감성품질 연구"],
                "flows": [{"title": "(목업) 더운 기후 시장에서 실내 공조 설계가 차별점이 되고 있다", "text": "목업 흐름 설명 문장입니다.", "ids": ids[:3]}]}

    def summary(self):
        return {"total_usd": round(self.spent, 4), "budget_usd": self.budget, "stages": {}}


def main():
    llm_mod.LLM = FakeLLM
    run_pipeline.LLM = FakeLLM
    process.get_body = lambda it: (it["snippet"], "abstract" if it["kind"] == "paper" else random.choice(["body", "snippet"]))
    base = datetime(2026, 11, 9, 20, 0, tzinfo=timezone.utc)
    for d in range(2):
        now = base + timedelta(days=d)
        day = now.date().isoformat()
        fetch.fetch_all = lambda now=None, day=day: fake_items(day)
        real_dt = run_pipeline.datetime

        class FixedDT(real_dt):
            @classmethod
            def now(cls, tz=None):
                return now.astimezone(tz) if tz else now
        run_pipeline.datetime = FixedDT
        run_pipeline.main()
        run_pipeline.datetime = real_dt


if __name__ == "__main__":
    main()
