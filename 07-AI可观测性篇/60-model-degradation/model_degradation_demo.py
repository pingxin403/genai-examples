"""
模型退化检测演示
对应文章：60-模型退化检测线上效果突然变差怎么发现
"""
from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field


@dataclass
class MetricSnapshot:
    hallucination_rate: float
    adoption_rate: float
    avg_latency_ms: float
    context_recall: float
    cost_per_request: float


@dataclass
class DriftAlert:
    metric: str
    baseline: float
    current: float
    deviation_pct: float
    severity: str
    causes: list[str] = field(default_factory=list)


class BaselineTracker:
    def __init__(self, window: int = 168):
        self.window = window
        self.data: dict[str, deque] = {}

    def update(self, metric: str, value: float):
        if metric not in self.data:
            self.data[metric] = deque(maxlen=self.window)
        self.data[metric].append(value)

    def stats(self, metric: str) -> dict:
        vals = list(self.data.get(metric, []))
        if len(vals) < 10:
            return {"mean": 0, "std": 0, "n": len(vals)}
        m = sum(vals) / len(vals)
        s = math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))
        return {"mean": round(m, 6), "std": round(s, 6), "n": len(vals)}


class DriftDetector:
    CAUSES = {
        "hallucination_rate": ["模型版本更新", "知识库过期", "RAG质量下降"],
        "adoption_rate": ["回答质量下降", "格式变化", "用户群变化"],
        "avg_latency_ms": ["服务负载增加", "Token增长", "并发上升"],
        "context_recall": ["知识库问题", "Embedding变化", "索引损坏"],
        "cost_per_request": ["Token增长", "定价变化", "缓存失效"],
    }

    def __init__(self, z_thresh: float = 2.5):
        self.z_thresh = z_thresh
        self.tracker = BaselineTracker()

    def feed(self, snap: MetricSnapshot):
        for attr in ["hallucination_rate", "adoption_rate",
                      "avg_latency_ms", "context_recall",
                      "cost_per_request"]:
            self.tracker.update(attr, getattr(snap, attr))

    def detect(self, snap: MetricSnapshot) -> list[DriftAlert]:
        alerts = []
        checks = [
            ("hallucination_rate", snap.hallucination_rate, True),
            ("adoption_rate", snap.adoption_rate, False),
            ("avg_latency_ms", snap.avg_latency_ms, True),
            ("context_recall", snap.context_recall, False),
            ("cost_per_request", snap.cost_per_request, True),
        ]
        for metric, val, higher_bad in checks:
            st = self.tracker.stats(metric)
            if st["n"] < 10 or st["std"] == 0:
                continue
            z = (val - st["mean"]) / st["std"]
            bad = z > self.z_thresh if higher_bad else z < -self.z_thresh
            if bad:
                dev = (val - st["mean"]) / st["mean"] * 100 if st["mean"] else 0
                alerts.append(DriftAlert(
                    metric=metric, baseline=st["mean"],
                    current=val, deviation_pct=round(dev, 2),
                    severity="P0" if abs(z) > 3.5 else "P1",
                    causes=self.CAUSES.get(metric, []),
                ))
        return alerts


class RegressionTester:
    def __init__(self, cases: list[dict]):
        self.cases = cases

    def run(self, model_fn) -> dict:
        passed = 0
        failed = []
        for c in self.cases:
            out = model_fn(c["query"])
            ok = bool(out and out.strip())
            if ok:
                passed += 1
            else:
                failed.append(c["query"])
        return {
            "total": len(self.cases),
            "passed": passed,
            "rate": round(passed / max(len(self.cases), 1), 4),
            "failed": failed,
        }


if __name__ == "__main__":
    detector = DriftDetector(z_thresh=2.5)

    print("=" * 60)
    print("模型退化检测演示")
    print("=" * 60)

    # 阶段1: 正常期 (模拟7天数据)
    print("\n📗 阶段1: 正常运行期 (168小时)")
    for _ in range(168):
        snap = MetricSnapshot(
            hallucination_rate=random.gauss(0.03, 0.005),
            adoption_rate=random.gauss(0.78, 0.03),
            avg_latency_ms=random.gauss(250, 30),
            context_recall=random.gauss(0.85, 0.03),
            cost_per_request=random.gauss(0.012, 0.002),
        )
        detector.feed(snap)

    # 检测正常数据
    normal_snap = MetricSnapshot(0.035, 0.76, 260, 0.83, 0.013)
    alerts = detector.detect(normal_snap)
    print(f"  正常快照检测: {len(alerts)} 告警 ✅")

    # 阶段2: 模型退化
    print("\n📕 阶段2: 模型退化 (模拟模型版本更新)")
    degraded_snap = MetricSnapshot(
        hallucination_rate=0.08,   # 从3%涨到8%
        adoption_rate=0.60,        # 从78%降到60%
        avg_latency_ms=280,
        context_recall=0.70,       # 从85%降到70%
        cost_per_request=0.015,
    )
    alerts = detector.detect(degraded_snap)
    print(f"  退化快照检测: {len(alerts)} 告警 🚨")
    for a in alerts:
        icon = "🔴" if a.severity == "P0" else "🟡"
        print(f"  {icon} [{a.severity}] {a.metric}: "
              f"基线={a.baseline:.4f} → 当前={a.current:.4f} "
              f"({a.deviation_pct:+.1f}%)")
        print(f"     可能原因: {', '.join(a.causes)}")

    # 回归测试
    print(f"\n{'='*60}")
    print("🧪 回归测试")
    tester = RegressionTester([
        {"query": "退货流程"},
        {"query": "产品保修期"},
        {"query": "配送时间"},
        {"query": "会员权益"},
        {"query": "发票申请"},
    ])

    def mock_model(q: str) -> str:
        if random.random() < 0.8:
            return f"关于{q}的回答..."
        return ""

    result = tester.run(mock_model)
    print(f"  通过率: {result['rate']:.0%} "
          f"({result['passed']}/{result['total']})")
    if result["failed"]:
        print(f"  失败用例: {result['failed']}")
