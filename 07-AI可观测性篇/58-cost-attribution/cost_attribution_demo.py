"""
成本拆分演示
对应文章：58-成本拆分每个用户的每次对话花了多少钱
"""
from __future__ import annotations

import random
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class TokenUsage:
    request_id: str
    user_id: str
    conversation_id: str
    scenario: str
    model: str
    component: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    timestamp: float = 0.0


class CostCalculator:
    PRICING = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "text-embedding-3-small": {"input": 0.00002, "output": 0},
    }

    def calculate(self, model: str, inp: int, out: int) -> float:
        p = self.PRICING.get(model, {"input": 0.002, "output": 0.008})
        return round(inp / 1000 * p["input"] + out / 1000 * p["output"], 6)


class CostAttributionEngine:
    def __init__(self):
        self.records: list[TokenUsage] = []
        self.calc = CostCalculator()

    def record(self, usage: TokenUsage):
        if usage.cost_usd == 0:
            usage.cost_usd = self.calc.calculate(
                usage.model, usage.input_tokens, usage.output_tokens)
        usage.timestamp = usage.timestamp or time.time()
        self.records.append(usage)

    def by_user(self) -> dict:
        agg: dict = defaultdict(lambda: {"cost": 0.0, "reqs": 0})
        for r in self.records:
            agg[r.user_id]["cost"] += r.cost_usd
            agg[r.user_id]["reqs"] += 1
        return {k: {"cost": round(v["cost"], 4), "reqs": v["reqs"]}
                for k, v in sorted(agg.items(),
                                   key=lambda x: x[1]["cost"], reverse=True)}

    def by_scenario(self) -> dict:
        agg: dict = defaultdict(lambda: {"cost": 0.0, "reqs": 0})
        for r in self.records:
            agg[r.scenario]["cost"] += r.cost_usd
            agg[r.scenario]["reqs"] += 1
        return {k: {"cost": round(v["cost"], 4), "reqs": v["reqs"],
                     "avg": round(v["cost"] / max(v["reqs"], 1), 6)}
                for k, v in agg.items()}

    def by_model(self) -> dict:
        agg: dict = defaultdict(lambda: {"cost": 0.0, "tokens": 0})
        for r in self.records:
            agg[r.model]["cost"] += r.cost_usd
            agg[r.model]["tokens"] += r.input_tokens + r.output_tokens
        return {k: {"cost": round(v["cost"], 4), "tokens": v["tokens"]}
                for k, v in agg.items()}

    def anomalies(self, mult: float = 5.0) -> list[dict]:
        if not self.records:
            return []
        avg = sum(r.cost_usd for r in self.records) / len(self.records)
        return [
            {"req": r.request_id, "user": r.user_id,
             "cost": round(r.cost_usd, 4),
             "x_avg": round(r.cost_usd / avg, 1)}
            for r in self.records if r.cost_usd > avg * mult
        ]

    def total(self) -> dict:
        return {
            "total_requests": len(self.records),
            "total_cost": round(sum(r.cost_usd for r in self.records), 4),
            "total_tokens": sum(
                r.input_tokens + r.output_tokens for r in self.records),
        }


def simulate(engine: CostAttributionEngine, n: int = 200):
    scenarios = ["customer_service", "search", "writing", "analysis"]
    models = ["gpt-4o", "gpt-4o-mini", "text-embedding-3-small"]
    users = [f"user-{i:03d}" for i in range(20)]

    for i in range(n):
        user = random.choice(users)
        scenario = random.choice(scenarios)
        model = random.choices(models, weights=[30, 50, 20])[0]
        inp = random.randint(100, 3000)
        out = random.randint(50, 800) if "embedding" not in model else 0
        engine.record(TokenUsage(
            request_id=f"req-{i:04d}",
            user_id=user,
            conversation_id=f"conv-{i // 3:04d}",
            scenario=scenario,
            model=model,
            component="llm" if "gpt" in model else "embedding",
            input_tokens=inp,
            output_tokens=out,
        ))

    # 注入几个异常高成本请求
    for j in range(3):
        engine.record(TokenUsage(
            request_id=f"req-anomaly-{j}",
            user_id="user-000",
            conversation_id=f"conv-anomaly-{j}",
            scenario="analysis",
            model="gpt-4o",
            component="llm",
            input_tokens=50000,
            output_tokens=5000,
        ))


if __name__ == "__main__":
    engine = CostAttributionEngine()

    print("=" * 60)
    print("AI成本拆分演示")
    print("=" * 60)

    simulate(engine)

    # 总览
    t = engine.total()
    print(f"\n📊 总览: {t['total_requests']} 请求, "
          f"${t['total_cost']}, {t['total_tokens']} tokens")

    # 按用户
    print("\n👤 Top 5 用户:")
    for i, (uid, data) in enumerate(list(engine.by_user().items())[:5]):
        print(f"  {i+1}. {uid}: ${data['cost']} ({data['reqs']} reqs)")

    # 按场景
    print("\n🎯 按场景:")
    for sc, data in engine.by_scenario().items():
        print(f"  {sc}: ${data['cost']} total, "
              f"${data['avg']} avg, {data['reqs']} reqs")

    # 按模型
    print("\n🤖 按模型:")
    for model, data in engine.by_model().items():
        print(f"  {model}: ${data['cost']}, {data['tokens']} tokens")

    # 异常检测
    anoms = engine.anomalies()
    print(f"\n⚠️ 异常请求 ({len(anoms)}):")
    for a in anoms:
        print(f"  {a['req']}: ${a['cost']} ({a['x_avg']}x平均)")
