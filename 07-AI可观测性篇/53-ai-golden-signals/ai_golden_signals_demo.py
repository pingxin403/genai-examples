"""
AI黄金信号采集演示
对应文章：53-AI黄金信号除了延迟错误还要看什么
"""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from enum import Enum


class SignalCategory(Enum):
    LATENCY = "latency"
    QUALITY = "quality"
    COST = "cost"
    ADOPTION = "adoption"


@dataclass
class AIGoldenSignals:
    """AI黄金信号"""
    # 延迟
    ttft_ms: float = 0.0
    tpot_ms: float = 0.0
    e2e_latency_ms: float = 0.0
    # 质量
    hallucination_rate: float = 0.0
    context_recall: float = 0.0
    format_compliance: float = 1.0
    refusal_rate: float = 0.0
    # 成本
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cache_hit: bool = False
    # 采纳
    adopted: bool = True
    thumbs_up: bool = False
    edited: bool = False


class AIMetricsCollector:
    """AI指标采集与聚合"""

    def __init__(self):
        self.metrics: list[AIGoldenSignals] = []

    def record(self, signals: AIGoldenSignals):
        self.metrics.append(signals)

    def summary(self) -> dict:
        if not self.metrics:
            return {}
        n = len(self.metrics)
        ttfts = [m.ttft_ms for m in self.metrics]
        e2es = [m.e2e_latency_ms for m in self.metrics]
        hall = [m.hallucination_rate for m in self.metrics]
        return {
            "total_requests": n,
            "avg_ttft_ms": round(statistics.mean(ttfts), 2),
            "p95_ttft_ms": round(sorted(ttfts)[int(n * 0.95)], 2),
            "avg_e2e_ms": round(statistics.mean(e2es), 2),
            "hallucination_rate": round(statistics.mean(hall), 4),
            "p99_hallucination": round(
                sorted(hall)[min(int(n * 0.99), n - 1)], 4
            ),
            "avg_context_recall": round(
                statistics.mean(m.context_recall for m in self.metrics), 4
            ),
            "total_tokens": sum(
                m.input_tokens + m.output_tokens for m in self.metrics
            ),
            "total_cost_usd": round(
                sum(m.cost_usd for m in self.metrics), 4
            ),
            "cache_hit_rate": round(
                sum(1 for m in self.metrics if m.cache_hit) / n, 4
            ),
            "adoption_rate": round(
                sum(1 for m in self.metrics if m.adopted) / n, 4
            ),
            "thumbs_up_rate": round(
                sum(1 for m in self.metrics if m.thumbs_up) / n, 4
            ),
        }

    def check_alerts(self, thresholds: dict) -> list[str]:
        alerts = []
        s = self.summary()
        if not s:
            return alerts
        if s["hallucination_rate"] > thresholds.get("max_hallucination", 0.05):
            alerts.append(
                f"⚠️ 幻觉率 {s['hallucination_rate']:.2%} 超过阈值 "
                f"{thresholds['max_hallucination']:.0%}"
            )
        if s["avg_ttft_ms"] > thresholds.get("max_ttft_ms", 500):
            alerts.append(
                f"⚠️ 平均TTFT {s['avg_ttft_ms']}ms 超过阈值"
            )
        if s["adoption_rate"] < thresholds.get("min_adoption", 0.6):
            alerts.append(
                f"⚠️ 采纳率 {s['adoption_rate']:.2%} 低于阈值"
            )
        if s["total_cost_usd"] > thresholds.get("max_cost_usd", 10):
            alerts.append(
                f"⚠️ 累计成本 ${s['total_cost_usd']} 超过预算"
            )
        return alerts


def detect_hallucination(response: str, context: str,
                         claims: list[str]) -> float:
    """简易幻觉检测"""
    if not claims:
        return 0.0
    unsupported = sum(
        1 for c in claims if c.lower() not in context.lower()
    )
    return unsupported / len(claims)


def simulate_request() -> AIGoldenSignals:
    """模拟一次AI请求的指标"""
    input_tok = random.randint(200, 2000)
    output_tok = random.randint(50, 500)
    cost = (input_tok * 0.000003) + (output_tok * 0.000015)
    return AIGoldenSignals(
        ttft_ms=random.uniform(50, 600),
        tpot_ms=random.uniform(10, 30),
        e2e_latency_ms=random.uniform(200, 3000),
        hallucination_rate=random.choices(
            [0.0, 0.02, 0.05, 0.1, 0.3],
            weights=[50, 25, 15, 8, 2],
        )[0],
        context_recall=random.uniform(0.6, 1.0),
        format_compliance=random.choices([1.0, 0.0], weights=[95, 5])[0],
        refusal_rate=random.choices([0.0, 1.0], weights=[97, 3])[0],
        input_tokens=input_tok,
        output_tokens=output_tok,
        cost_usd=cost,
        cache_hit=random.random() < 0.3,
        adopted=random.random() < 0.75,
        thumbs_up=random.random() < 0.4,
        edited=random.random() < 0.2,
    )


if __name__ == "__main__":
    collector = AIMetricsCollector()

    print("=" * 60)
    print("AI黄金信号采集演示")
    print("=" * 60)

    # 模拟100次请求
    for _ in range(100):
        signals = simulate_request()
        collector.record(signals)

    # 输出摘要
    summary = collector.summary()
    print("\n📊 指标摘要:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    # 检查告警
    thresholds = {
        "max_hallucination": 0.05,
        "max_ttft_ms": 400,
        "min_adoption": 0.7,
        "max_cost_usd": 0.5,
    }
    alerts = collector.check_alerts(thresholds)
    print(f"\n🚨 告警 ({len(alerts)}):")
    for a in alerts:
        print(f"  {a}")

    # 幻觉检测示例
    print("\n" + "=" * 60)
    print("幻觉检测示例")
    context = "我们的退货政策是30天内可退，需要保留原包装。"
    response = "退货政策是60天内可退，无需原包装。"
    claims = ["60天内可退", "无需原包装"]
    rate = detect_hallucination(response, context, claims)
    print(f"  上下文: {context}")
    print(f"  回答声明: {claims}")
    print(f"  幻觉率: {rate:.0%}")
