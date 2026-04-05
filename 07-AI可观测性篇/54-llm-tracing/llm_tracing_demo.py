"""
LLM调用追踪演示
对应文章：54-LLM调用追踪把Prompt和Completion打进Trace
"""
from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass, field


@dataclass
class LLMSpan:
    """LLM调用Span"""
    trace_id: str
    span_id: str
    parent_span_id: str = ""
    operation: str = "llm.chat"
    model: str = ""
    prompt_summary: str = ""
    completion_summary: str = ""
    prompt_hash: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    temperature: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    labels: dict = field(default_factory=dict)


class LLMTracer:
    """LLM调用追踪器"""

    PRICING = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    }

    def __init__(self, sampling_rate: float = 0.1):
        self.spans: list[LLMSpan] = []
        self.sampling_rate = sampling_rate

    def start_span(self, trace_id: str, model: str,
                   prompt: str, **kwargs) -> LLMSpan:
        span_id = hashlib.md5(
            f"{trace_id}-{time.time()}-{random.random()}".encode()
        ).hexdigest()[:16]
        summary = prompt[:150] + "..." if len(prompt) > 150 else prompt
        return LLMSpan(
            trace_id=trace_id,
            span_id=span_id,
            model=model,
            prompt_summary=summary,
            prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()[:16],
            temperature=kwargs.get("temperature", 0.7),
            start_time=time.time(),
            labels=kwargs.get("labels", {}),
        )

    def end_span(self, span: LLMSpan, completion: str,
                 prompt_tokens: int, completion_tokens: int):
        span.end_time = time.time()
        span.duration_ms = round((span.end_time - span.start_time) * 1000, 2)
        span.completion_summary = (
            completion[:150] + "..." if len(completion) > 150 else completion
        )
        span.prompt_tokens = prompt_tokens
        span.completion_tokens = completion_tokens
        span.total_tokens = prompt_tokens + completion_tokens
        span.cost_usd = self._calc_cost(span.model, prompt_tokens,
                                        completion_tokens)
        # 分层采样
        if self._should_sample(span):
            self.spans.append(span)

    def _calc_cost(self, model: str, inp: int, out: int) -> float:
        p = self.PRICING.get(model, {"input": 0.002, "output": 0.008})
        return round((inp / 1000 * p["input"]) + (out / 1000 * p["output"]), 6)

    def _should_sample(self, span: LLMSpan) -> bool:
        if span.labels.get("error"):
            return True
        if span.cost_usd > 0.05:
            return True
        return random.random() < self.sampling_rate

    def get_trace(self, trace_id: str) -> list[LLMSpan]:
        return [s for s in self.spans if s.trace_id == trace_id]

    def cost_summary(self) -> dict:
        by_model: dict[str, float] = {}
        for s in self.spans:
            by_model[s.model] = by_model.get(s.model, 0) + s.cost_usd
        return {
            "total_spans": len(self.spans),
            "total_cost_usd": round(sum(s.cost_usd for s in self.spans), 4),
            "by_model": {k: round(v, 4) for k, v in by_model.items()},
        }


def simulate_llm_call(tracer: LLMTracer, trace_id: str):
    """模拟一次LLM调用"""
    models = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet"]
    model = random.choice(models)
    prompt = f"用户问题: {random.choice(['退货流程', '产品价格', '配送时间', '售后服务'])}"
    span = tracer.start_span(trace_id, model, prompt,
                             labels={"scenario": "customer_service"})
    time.sleep(random.uniform(0.01, 0.05))
    completion = f"关于您的问题，{random.choice(['以下是详细说明...', '请参考以下步骤...'])}"
    tracer.end_span(span, completion,
                    prompt_tokens=random.randint(100, 2000),
                    completion_tokens=random.randint(50, 500))


if __name__ == "__main__":
    tracer = LLMTracer(sampling_rate=1.0)  # 演示用100%采样

    print("=" * 60)
    print("LLM调用追踪演示")
    print("=" * 60)

    # 模拟20次调用
    for i in range(20):
        tid = f"trace-{i:04d}"
        simulate_llm_call(tracer, tid)

    # 展示Span详情
    print(f"\n📋 采集到 {len(tracer.spans)} 个Span:")
    for s in tracer.spans[:5]:
        print(f"\n  Trace: {s.trace_id} | Model: {s.model}")
        print(f"  Prompt: {s.prompt_summary}")
        print(f"  Tokens: {s.prompt_tokens}+{s.completion_tokens}"
              f"={s.total_tokens}")
        print(f"  Cost: ${s.cost_usd:.4f} | Duration: {s.duration_ms}ms")

    # 成本摘要
    print(f"\n{'='*60}")
    print("💰 成本摘要:")
    cs = tracer.cost_summary()
    for k, v in cs.items():
        print(f"  {k}: {v}")
