"""
AI告警设计演示
对应文章：56-AI告警设计幻觉率大于5成本突增该告警了
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from enum import Enum


class AlertSeverity(Enum):
    P0_CRITICAL = "P0"
    P1_WARNING = "P1"
    P2_INFO = "P2"


@dataclass
class AlertRule:
    name: str
    metric: str
    severity: AlertSeverity
    threshold: float
    comparison: str  # gt / lt
    description: str = ""


@dataclass
class Alert:
    rule_name: str
    severity: AlertSeverity
    metric: str
    current_value: float
    threshold: float
    message: str = ""


class AIAlertEngine:
    def __init__(self):
        self.rules: list[AlertRule] = []
        self.alerts: list[Alert] = []
        self._init_rules()

    def _init_rules(self):
        self.rules = [
            AlertRule("幻觉率紧急", "hallucination_rate",
                      AlertSeverity.P0_CRITICAL, 0.10, "gt",
                      "幻觉率>10%，立即处理"),
            AlertRule("幻觉率警告", "hallucination_rate",
                      AlertSeverity.P1_WARNING, 0.05, "gt",
                      "幻觉率>5%，需关注"),
            AlertRule("采纳率过低", "adoption_rate",
                      AlertSeverity.P1_WARNING, 0.50, "lt",
                      "采纳率<50%"),
            AlertRule("成本燃烧率", "cost_burn_rate",
                      AlertSeverity.P0_CRITICAL, 3.0, "gt",
                      "成本消耗速率>3x预算"),
            AlertRule("TTFT过高", "ttft_p95_ms",
                      AlertSeverity.P2_INFO, 1000, "gt",
                      "首Token延迟P95>1s"),
            AlertRule("日成本超预算", "daily_cost_ratio",
                      AlertSeverity.P1_WARNING, 1.5, "gt",
                      "日成本>预算150%"),
        ]

    def evaluate(self, metrics: dict) -> list[Alert]:
        fired = []
        for rule in self.rules:
            val = metrics.get(rule.metric)
            if val is None:
                continue
            triggered = (val > rule.threshold if rule.comparison == "gt"
                         else val < rule.threshold)
            if triggered:
                alert = Alert(
                    rule_name=rule.name,
                    severity=rule.severity,
                    metric=rule.metric,
                    current_value=val,
                    threshold=rule.threshold,
                    message=f"{rule.description} "
                            f"(当前={val:.4f}, 阈值={rule.threshold})",
                )
                fired.append(alert)
                self.alerts.append(alert)
        return fired


class BurnRateCalculator:
    def __init__(self, daily_budget: float):
        self.daily_budget = daily_budget
        self.hourly_costs: list[float] = []

    def add_hour(self, cost: float):
        self.hourly_costs.append(cost)

    def burn_rate(self) -> float:
        if not self.hourly_costs:
            return 0.0
        expected = self.daily_budget / 24
        actual = self.hourly_costs[-1]
        return actual / expected if expected > 0 else 0.0

    def projected_daily(self) -> float:
        if not self.hourly_costs:
            return 0.0
        return (sum(self.hourly_costs) / len(self.hourly_costs)) * 24

    def status(self) -> dict:
        proj = self.projected_daily()
        return {
            "budget": self.daily_budget,
            "projected": round(proj, 2),
            "burn_rate": round(self.burn_rate(), 2),
            "over_budget": proj > self.daily_budget,
        }


if __name__ == "__main__":
    engine = AIAlertEngine()

    print("=" * 60)
    print("AI告警引擎演示")
    print("=" * 60)

    # 场景1: 正常指标
    normal = {
        "hallucination_rate": 0.03,
        "adoption_rate": 0.75,
        "cost_burn_rate": 1.1,
        "ttft_p95_ms": 350,
        "daily_cost_ratio": 0.8,
    }
    alerts = engine.evaluate(normal)
    print(f"\n✅ 正常场景: {len(alerts)} 条告警")

    # 场景2: 幻觉率飙升
    bad_quality = {
        "hallucination_rate": 0.12,
        "adoption_rate": 0.45,
        "cost_burn_rate": 1.5,
        "ttft_p95_ms": 800,
        "daily_cost_ratio": 1.2,
    }
    alerts = engine.evaluate(bad_quality)
    print(f"\n🚨 质量退化场景: {len(alerts)} 条告警")
    for a in alerts:
        icon = "🔴" if a.severity == AlertSeverity.P0_CRITICAL else "🟡"
        print(f"  {icon} [{a.severity.value}] {a.message}")

    # 场景3: 成本失控
    cost_spike = {
        "hallucination_rate": 0.04,
        "adoption_rate": 0.70,
        "cost_burn_rate": 4.5,
        "ttft_p95_ms": 1200,
        "daily_cost_ratio": 2.0,
    }
    alerts = engine.evaluate(cost_spike)
    print(f"\n💸 成本失控场景: {len(alerts)} 条告警")
    for a in alerts:
        icon = "🔴" if a.severity == AlertSeverity.P0_CRITICAL else "🟡"
        print(f"  {icon} [{a.severity.value}] {a.message}")

    # 燃烧率计算
    print(f"\n{'='*60}")
    print("💰 成本燃烧率分析")
    calc = BurnRateCalculator(daily_budget=100.0)
    for h in range(8):
        cost = random.uniform(3.0, 8.0)
        calc.add_hour(cost)
        print(f"  第{h+1}小时: ${cost:.2f}")

    status = calc.status()
    print(f"\n  预算状态:")
    for k, v in status.items():
        print(f"    {k}: {v}")
