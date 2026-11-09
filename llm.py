"""Claude 호출 래퍼: 실측 사용량 기록 + 실행 예산 가드."""
import json
import os
import re
from datetime import datetime, timezone

import config


class BudgetExceeded(Exception):
    pass


class LLM:
    def __init__(self, usage_path="data/usage.jsonl", budget=config.RUN_BUDGET_USD):
        import anthropic
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.usage_path = usage_path
        self.budget = budget
        self.spent = 0.0
        self.calls = []

    def cost(self, model, u):
        p = config.PRICES[model]
        cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
        return (u.input_tokens * p["in"] + cache_read * p["cache_read"] + u.output_tokens * p["out"]) / 1e6

    def json_call(self, *, model, system, user, max_tokens, stage, schema):
        """도구 호출을 강제해 항상 유효한 JSON(schema)을 받는다."""
        if self.spent >= self.budget:
            raise BudgetExceeded(f"{self.spent:.4f} >= {self.budget}")
        msg = self.client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
            tools=[{"name": "output", "description": "결과를 제출한다", "input_schema": schema}],
            tool_choice={"type": "tool", "name": "output"},
        )
        c = self.cost(model, msg.usage)
        self.spent += c
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(), "stage": stage, "model": model,
            "input": msg.usage.input_tokens, "output": msg.usage.output_tokens,
            "cache_read": getattr(msg.usage, "cache_read_input_tokens", 0) or 0,
            "usd": round(c, 6), "measured": True, "prices_checked": config.PRICES_CHECKED,
        }
        self.calls.append(rec)
        os.makedirs(os.path.dirname(self.usage_path), exist_ok=True)
        with open(self.usage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if msg.stop_reason == "max_tokens":
            print(f"[WARN] {stage}: 출력이 max_tokens에서 잘림")
        for b in msg.content:
            if getattr(b, "type", "") == "tool_use":
                return b.input
        raise ValueError(f"{stage}: tool_use 응답 없음")

    def summary(self):
        by = {}
        for r in self.calls:
            s = by.setdefault(r["stage"], {"calls": 0, "input": 0, "output": 0, "usd": 0.0})
            s["calls"] += 1
            s["input"] += r["input"]
            s["output"] += r["output"]
            s["usd"] += r["usd"]
        return {"total_usd": round(self.spent, 4), "budget_usd": self.budget, "stages": by}


def parse_json(text):
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    start = min([i for i in (text.find("["), text.find("{")) if i >= 0], default=0)
    return json.loads(text[start:])
