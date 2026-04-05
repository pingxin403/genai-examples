"""
AI成本控制面板演示：计量采集 + 多维聚合 + 预算预警
对应文章：74-AI成本控制面板实时看Token消耗预算预警
"""
from __future__ import annotations

import time
import random
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class UsageRecord:
    timestamp: float
    team: str
    scene: str
    model: str
    user_id: str
    prompt_tokens: int
    completion_tokens: int
    cost: float


class CostCollector:
    PRICING = {
        "gpt-4o": (0.005, 0.015),
        "gpt-4o-mini": (0.00015, 0.0006),
        "claude-3.5": (0.003, 0.015),
        "llama-3": (0.0005, 0.001),
    }

    def __init__(self):
        self.records: list[UsageRecord] = []

    def record(self, team, scene, model, user_id, prompt_tok, comp_tok):
        p = self.PRICING.get(model, (0.01, 0.03))
        cost = prompt_tok / 1000 * p[0] + comp_tok / 1000 * p[1]
        r = UsageRecord(time.time(), team, scene, model, user_id,
                        prompt_tok, comp_tok, round(cost, 6))
        self.records.append(r)
        return r


class CostAggregator:
    def __init__(self, collector: CostCollector):
        self.c = collector

    def by_team(self):
        agg = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})
        for r in self.c.records:
            a = agg[r.team]
            a["calls"] += 1
            a["tokens"] += r.prompt_tokens + r.completion_tokens
            a["cost"] += r.cost
        return {k: {**v, "cost": round(v["cost"], 4)} for k, v in agg.items()}

    def by_scene(self):
        agg = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})
        for r in self.c.records:
            a = agg[r.scene]
            a["calls"] += 1
            a["tokens"] += r.prompt_tokens + r.completion_tokens
            a["cost"] += r.cost
        return {k: {**v, "cost": round(v["cost"], 4)} for k, v in agg.items()}

    def by_model(self):
        agg = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})
        for r in self.c.records:
            a = agg[r.model]
            a["calls"] += 1
            a["tokens"] += r.prompt_tokens + r.completion_tokens
            a["cost"] += r.cost
        return {k: {**v, "cost": round(v["cost"], 4)} for k, v in agg.items()}

    def top_users(self, n=5):
        agg = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})
        for r in self.c.records:
            a = agg[r.user_id]
            a["calls"] += 1
            a["tokens"] += r.prompt_tokens + r.completion_tokens
            a["cost"] += r.cost
        ranked = sorted(agg.items(), key=lambda x: x[1]["cost"], reverse=True)
        return [{"user": k, **v, "cost": round(v["cost"], 4)} for k, v in ranked[:n]]

    def total(self):
        return round(sum(r.cost for r in self.c.records), 4)


class BudgetAlertManager:
    def __init__(self, agg: CostAggregator):
        self.agg = agg
        self.budgets: dict[str, float] = {}

    def set_budget(self, team, budget):
        self.budgets[team] = budget

    def check(self):
        team_costs = self.agg.by_team()
        alerts = []
        for team, budget in self.budgets.items():
            cost = team_costs.get(team, {}).get("cost", 0.0)
            pct = (cost / budget * 100) if budget > 0 else 0
            if pct >= 100:
                level = "🔴 CRITICAL"
            elif pct >= 80:
                level = "🟡 WARNING"
            elif pct >= 60:
                level = "🔵 INFO"
            else:
                continue
            alerts.append({
                "team": team, "level": level,
                "used": round(cost, 4), "budget": budget,
                "pct": round(pct, 1),
            })
        return alerts

    def suggestions(self):
        tips = []
        models = self.agg.by_model()
        total = self.agg.total()
        if "gpt-4o" in models and total > 0:
            ratio = models["gpt-4o"]["cost"] / total * 100
            if ratio > 50:
                tips.append(f"💡 GPT-4o占总成本{ratio:.0f}%，建议简单任务降级到gpt-4o-mini")
        users = self.agg.top_users(1)
        if users:
            tips.append(f"💡 用户{users[0]['user']}消耗最高(${users[0]['cost']})，建议检查异常调用")
        return tips


def main():
    collector = CostCollector()
    agg = CostAggregator(collector)
    alerts = BudgetAlertManager(agg)

    print("=" * 60)
    print("AI成本控制面板演示")
    print("=" * 60)

    # 模拟调用数据
    calls = [
        ("customer_service", "faq", "gpt-4o", "u1", 500, 200),
        ("customer_service", "faq", "gpt-4o", "u2", 600, 250),
        ("customer_service", "complaint", "gpt-4o", "u1", 800, 400),
        ("sales", "competitor_analysis", "gpt-4o", "u3", 2000, 1500),
        ("sales", "competitor_analysis", "gpt-4o", "u3", 2500, 1800),
        ("sales", "product_qa", "gpt-4o-mini", "u4", 300, 150),
        ("hr", "policy_qa", "llama-3", "u5", 400, 200),
        ("hr", "policy_qa", "llama-3", "u6", 350, 180),
        ("legal", "contract_review", "claude-3.5", "u7", 3000, 1000),
        ("legal", "contract_review", "claude-3.5", "u7", 2800, 900),
    ]

    print("\n--- 1. 记录AI调用 ---")
    for team, scene, model, uid, pt, ct in calls:
        r = collector.record(team, scene, model, uid, pt, ct)
        print(f"  [{team}/{scene}] {model} user={uid} "
              f"tokens={pt+ct} cost=${r.cost:.4f}")

    # 按维度聚合
    print(f"\n--- 2. 按团队聚合 ---")
    for team, data in agg.by_team().items():
        print(f"  [{team}] calls={data['calls']} tokens={data['tokens']} cost=${data['cost']}")

    print(f"\n--- 3. 按场景聚合 ---")
    for scene, data in agg.by_scene().items():
        print(f"  [{scene}] calls={data['calls']} tokens={data['tokens']} cost=${data['cost']}")

    print(f"\n--- 4. 按模型聚合 ---")
    for model, data in agg.by_model().items():
        print(f"  [{model}] calls={data['calls']} tokens={data['tokens']} cost=${data['cost']}")

    print(f"\n--- 5. Top消耗用户 ---")
    for u in agg.top_users(5):
        print(f"  [{u['user']}] calls={u['calls']} tokens={u['tokens']} cost=${u['cost']}")

    print(f"\n  总成本: ${agg.total()}")

    # 预算预警
    print(f"\n--- 6. 预算预警 ---")
    alerts.set_budget("customer_service", 0.02)
    alerts.set_budget("sales", 0.05)
    alerts.set_budget("hr", 0.01)
    alerts.set_budget("legal", 0.10)

    for a in alerts.check():
        print(f"  {a['level']} [{a['team']}] ${a['used']}/{a['budget']} ({a['pct']}%)")

    # 优化建议
    print(f"\n--- 7. 优化建议 ---")
    for tip in alerts.suggestions():
        print(f"  {tip}")


if __name__ == "__main__":
    main()
