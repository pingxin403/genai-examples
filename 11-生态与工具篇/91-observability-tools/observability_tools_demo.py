"""
可观测性工具对比演示：Datadog AI vs 自建OTel扩展
模拟两种AI可观测性方案的核心能力
"""

import time
import random
from dataclasses import dataclass, field


# ============================================================
# Datadog AI Monitoring 风格
# ============================================================
@dataclass
class LLMSpan:
    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    duration_ms: float
    metadata: dict = field(default_factory=dict)


class DatadogStyleMonitor:
    """模拟Datadog AI Monitoring的自动采集"""

    def __init__(self):
        self.spans: list[LLMSpan] = []
        self.metrics: dict[str, list[float]] = {}

    def trace_llm_call(self, model: str, input_tokens: int,
                       output_tokens: int, duration_ms: float):
        span = LLMSpan(
            operation="llm.completion", model=model,
            input_tokens=input_tokens, output_tokens=output_tokens,
            duration_ms=duration_ms,
        )
        self.spans.append(span)
        self._record("llm.latency_ms", duration_ms)
        self._record("llm.tokens.input", input_tokens)
        self._record("llm.tokens.output", output_tokens)
        cost = (input_tokens * 0.03 + output_tokens * 0.06) / 1000
        self._record("llm.cost_usd", cost)

    def _record(self, name: str, value: float):
        self.metrics.setdefault(name, []).append(value)

    def dashboard(self) -> dict:
        result = {}
        for name, values in self.metrics.items():
            sv = sorted(values)
            result[name] = {
                "avg": round(sum(values) / len(values), 4),
                "p95": round(sv[int(len(sv) * 0.95)] if sv else 0, 4),
                "total": round(sum(values), 4),
                "count": len(values),
            }
        return result


# ============================================================
# OpenTelemetry 自建方案
# ============================================================
class OTelAIExtension:
    """基于OTel的AI可观测性扩展"""

    def __init__(self):
        self.traces: list[dict] = []
        self.metrics: dict[str, list[dict]] = {}

    def start_span(self, name: str, attributes: dict = None) -> dict:
        return {
            "name": name,
            "start_time": time.time(),
            "attributes": attributes or {},
            "events": [],
        }

    def end_span(self, span: dict):
        span["end_time"] = time.time()
        span["duration_ms"] = round((span["end_time"] - span["start_time"]) * 1000, 2)
        self.traces.append(span)

    def record_llm(self, model: str, input_tokens: int,
                   output_tokens: int, latency_ms: float):
        self._add("ai.llm.input_tokens", input_tokens, {"model": model})
        self._add("ai.llm.output_tokens", output_tokens, {"model": model})
        self._add("ai.llm.latency_ms", latency_ms, {"model": model})

    def record_rag(self, hit_rate: float, relevance: float):
        self._add("ai.rag.hit_rate", hit_rate)
        self._add("ai.rag.relevance", relevance)

    def record_hallucination(self, is_hallucination: bool):
        self._add("ai.hallucination", 1 if is_hallucination else 0)

    def _add(self, name: str, value, labels: dict = None):
        self.metrics.setdefault(name, []).append({"value": value, "labels": labels or {}})

    def health_report(self) -> dict:
        report = {}
        for name, entries in self.metrics.items():
            values = [e["value"] for e in entries]
            report[name] = {
                "avg": round(sum(values) / len(values), 4) if values else 0,
                "count": len(values),
                "sum": round(sum(values), 4),
            }
        return report


# ============================================================
# 模拟AI应用产生遥测数据
# ============================================================
def simulate_workload(dd: DatadogStyleMonitor, otel: OTelAIExtension, n: int = 30):
    models = ["gpt-4o", "gpt-4o-mini", "claude-3-sonnet"]
    for _ in range(n):
        model = random.choice(models)
        input_t = random.randint(200, 2000)
        output_t = random.randint(50, 500)
        latency = random.uniform(100, 3000)

        # Datadog采集
        dd.trace_llm_call(model, input_t, output_t, latency)

        # OTel采集
        span = otel.start_span("llm.call", {"model": model})
        otel.record_llm(model, input_t, output_t, latency)
        otel.record_rag(random.uniform(0.6, 1.0), random.uniform(0.5, 1.0))
        otel.record_hallucination(random.random() < 0.05)
        otel.end_span(span)


# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 60)
    print("AI可观测性工具对比演示")
    print("=" * 60)

    dd = DatadogStyleMonitor()
    otel = OTelAIExtension()
    simulate_workload(dd, otel, n=30)

    # Datadog Dashboard
    print("\n--- Datadog AI Dashboard ---")
    for name, stats in dd.dashboard().items():
        print(f"  {name:<24} avg={stats['avg']:<10} p95={stats['p95']:<10} "
              f"total={stats['total']:<10} count={stats['count']}")

    # OTel Health Report
    print("\n--- OTel AI Health Report ---")
    for name, stats in otel.health_report().items():
        print(f"  {name:<28} avg={stats['avg']:<10} count={stats['count']:<6} "
              f"sum={stats['sum']}")

    # 对比
    print("\n" + "=" * 60)
    print("方案对比")
    print("=" * 60)
    rows = [
        ("搭建时间", "1天", "2-4周"),
        ("月成本(10万调用/天)", "$2000+", "$300(基础设施)"),
        ("AI指标覆盖", "80%内置", "100%自定义"),
        ("数据主权", "在Datadog", "在自己手里"),
        ("定制能力", "有限", "完全自定义"),
    ]
    print(f"{'维度':<24} {'Datadog':<20} {'OTel自建'}")
    print("-" * 60)
    for dim, dd_val, otel_val in rows:
        print(f"{dim:<24} {dd_val:<20} {otel_val}")


if __name__ == "__main__":
    main()
