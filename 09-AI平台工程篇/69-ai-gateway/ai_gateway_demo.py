"""
AI Gateway演示：多模型路由 + 降级 + 缓存 + 配额
对应文章：69-AI-Gateway统一的模型接入路由降级层
"""
from __future__ import annotations

import time
import hashlib
import json
import random
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict


class ModelProvider(Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    LOCAL = "local"
    QWEN = "qwen"


class ModelStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class RoutingStrategy(Enum):
    PRIORITY = "priority"
    COST_OPTIMIZED = "cost"
    LATENCY_OPTIMIZED = "latency"
    WEIGHTED = "weighted"


@dataclass
class ModelEndpoint:
    provider: ModelProvider
    model_name: str
    priority: int = 0
    weight: float = 1.0
    max_tokens_per_min: int = 100000
    cost_per_1k_input: float = 0.01
    cost_per_1k_output: float = 0.03
    status: ModelStatus = ModelStatus.HEALTHY
    error_count: int = 0
    avg_latency_ms: float = 200.0


class RoutingEngine:
    def __init__(self):
        self.endpoints: list[ModelEndpoint] = []
        self.circuit_breakers: dict[str, dict] = {}

    def add_endpoint(self, ep: ModelEndpoint):
        self.endpoints.append(ep)
        key = f"{ep.provider.value}:{ep.model_name}"
        self.circuit_breakers[key] = {
            "failures": 0, "threshold": 3,
            "reset_time": 60, "last_failure": 0, "state": "closed",
        }

    def route(self, strategy: RoutingStrategy):
        available = [
            e for e in self.endpoints
            if e.status != ModelStatus.DOWN and not self._is_open(e)
        ]
        if not available:
            return None
        if strategy == RoutingStrategy.PRIORITY:
            return min(available, key=lambda e: e.priority)
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            return min(available, key=lambda e: e.cost_per_1k_input)
        elif strategy == RoutingStrategy.LATENCY_OPTIMIZED:
            return min(available, key=lambda e: e.avg_latency_ms)
        else:
            return self._weighted(available)

    def _weighted(self, eps):
        total = sum(e.weight for e in eps)
        r = random.random() * total
        c = 0
        for e in eps:
            c += e.weight
            if r <= c:
                return e
        return eps[-1]

    def _is_open(self, ep):
        key = f"{ep.provider.value}:{ep.model_name}"
        cb = self.circuit_breakers[key]
        if cb["state"] == "open":
            if time.time() - cb["last_failure"] > cb["reset_time"]:
                cb["state"] = "half-open"
                return False
            return True
        return False

    def report_failure(self, ep):
        key = f"{ep.provider.value}:{ep.model_name}"
        cb = self.circuit_breakers[key]
        cb["failures"] += 1
        cb["last_failure"] = time.time()
        if cb["failures"] >= cb["threshold"]:
            cb["state"] = "open"
            ep.status = ModelStatus.DOWN

    def report_success(self, ep):
        key = f"{ep.provider.value}:{ep.model_name}"
        cb = self.circuit_breakers[key]
        cb["failures"] = 0
        cb["state"] = "closed"
        ep.status = ModelStatus.HEALTHY


class AIGateway:
    def __init__(self):
        self.router = RoutingEngine()
        self.cache: dict[str, dict] = {}
        self.quotas: dict[str, dict] = {}
        self.metrics: list[dict] = []

    def call(self, prompt: str, team: str = "default",
             strategy: RoutingStrategy = RoutingStrategy.PRIORITY,
             max_retries: int = 3) -> dict:
        if not self._check_quota(team):
            return {"error": "quota_exceeded", "message": "团队配额已用完"}

        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        if cache_key in self.cache:
            self._record("cache_hit", team, 0, 0)
            return {**self.cache[cache_key], "cached": True}

        for _ in range(max_retries):
            ep = self.router.route(strategy)
            if not ep:
                return {"error": "no_available_model"}
            result = self._invoke(ep, prompt)
            if result.get("success"):
                self.router.report_success(ep)
                self._update_quota(team, result["tokens"])
                self.cache[cache_key] = result
                self._record("success", team, result["latency_ms"], result["tokens"])
                return result
            else:
                self.router.report_failure(ep)

        return {"error": "all_models_failed"}

    def _invoke(self, ep: ModelEndpoint, prompt: str) -> dict:
        latency = ep.avg_latency_ms + random.uniform(-50, 50)
        tokens = len(prompt.split()) * 3
        return {
            "success": True,
            "content": f"[{ep.provider.value}/{ep.model_name}] 回答: {prompt[:40]}...",
            "model": ep.model_name, "provider": ep.provider.value,
            "tokens": tokens, "latency_ms": round(latency, 1),
            "cost": round(tokens / 1000 * ep.cost_per_1k_output, 4),
        }

    def set_quota(self, team: str, daily_tokens: int):
        self.quotas[team] = {"limit": daily_tokens, "used": 0}

    def _check_quota(self, team: str) -> bool:
        if team not in self.quotas:
            return True
        return self.quotas[team]["used"] < self.quotas[team]["limit"]

    def _update_quota(self, team: str, tokens: int):
        if team in self.quotas:
            self.quotas[team]["used"] += tokens

    def _record(self, event_type: str, team: str, latency: float, tokens: int):
        self.metrics.append({
            "type": event_type, "team": team,
            "latency_ms": latency, "tokens": tokens,
            "ts": time.time(),
        })

    def get_stats(self) -> dict:
        stats = defaultdict(lambda: {"calls": 0, "tokens": 0, "cache_hits": 0})
        for m in self.metrics:
            s = stats[m["team"]]
            s["calls"] += 1
            s["tokens"] += m["tokens"]
            if m["type"] == "cache_hit":
                s["cache_hits"] += 1
        return dict(stats)


def main():
    gw = AIGateway()

    # 注册模型端点
    gw.router.add_endpoint(ModelEndpoint(
        ModelProvider.OPENAI, "gpt-4o", priority=1,
        cost_per_1k_input=0.005, cost_per_1k_output=0.015, avg_latency_ms=300,
    ))
    gw.router.add_endpoint(ModelEndpoint(
        ModelProvider.CLAUDE, "claude-3.5-sonnet", priority=2,
        cost_per_1k_input=0.003, cost_per_1k_output=0.015, avg_latency_ms=350,
    ))
    gw.router.add_endpoint(ModelEndpoint(
        ModelProvider.LOCAL, "llama-3-8b", priority=3,
        cost_per_1k_input=0.0005, cost_per_1k_output=0.001, avg_latency_ms=100,
    ))
    gw.router.add_endpoint(ModelEndpoint(
        ModelProvider.QWEN, "qwen-plus", priority=2,
        cost_per_1k_input=0.002, cost_per_1k_output=0.006, avg_latency_ms=250,
    ))

    # 设置配额
    gw.set_quota("customer_service", daily_tokens=10000)
    gw.set_quota("doc_team", daily_tokens=5000)

    print("=" * 60)
    print("AI Gateway 演示")
    print("=" * 60)

    # 1. 多策略路由
    print("\n--- 1. 多策略路由 ---")
    for strategy in RoutingStrategy:
        result = gw.call(f"用{strategy.value}策略回答问题", "customer_service", strategy)
        if result.get("success"):
            print(f"  [{strategy.value}] -> {result['provider']}/{result['model']} "
                  f"延迟={result['latency_ms']}ms 成本=${result['cost']}")

    # 2. 缓存命中
    print("\n--- 2. 缓存命中 ---")
    prompt = "退货流程是什么？"
    r1 = gw.call(prompt, "customer_service")
    print(f"  首次调用: cached={r1.get('cached', False)}")
    r2 = gw.call(prompt, "customer_service")
    print(f"  重复调用: cached={r2.get('cached', False)}")

    # 3. 模型故障降级
    print("\n--- 3. 模型故障降级 ---")
    openai_ep = gw.router.endpoints[0]
    openai_ep.status = ModelStatus.DOWN
    print(f"  模拟OpenAI故障...")
    result = gw.call("故障后的请求", "customer_service")
    if result.get("success"):
        print(f"  自动降级到: {result['provider']}/{result['model']}")
    openai_ep.status = ModelStatus.HEALTHY

    # 4. 配额限制
    print("\n--- 4. 配额限制 ---")
    gw.set_quota("test_team", daily_tokens=50)
    for i in range(5):
        r = gw.call(f"配额测试请求 {i}", "test_team")
        status = "成功" if r.get("success") else r.get("error", "unknown")
        print(f"  请求{i+1}: {status}")

    # 5. 调用统计
    print("\n--- 5. 调用统计 ---")
    stats = gw.get_stats()
    for team, s in stats.items():
        print(f"  [{team}] 调用={s['calls']} Token={s['tokens']} 缓存命中={s['cache_hits']}")


if __name__ == "__main__":
    main()
