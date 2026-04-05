"""
模型路由策略演示：场景分类 + 多因素评分 + 降级
对应文章：75-模型路由策略按场景按成本按延迟自动调度
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from enum import Enum
from collections import Counter


class SceneType(Enum):
    SIMPLE_QA = "simple_qa"
    COMPLEX_REASONING = "complex_reasoning"
    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"
    CREATIVE_WRITING = "creative_writing"


class SceneClassifier:
    PATTERNS = {
        SceneType.SIMPLE_QA: [r"是什么", r"怎么", r"多少", r"在哪"],
        SceneType.CODE_GENERATION: [r"写.*代码", r"实现.*函数", r"编程"],
        SceneType.SUMMARIZATION: [r"总结", r"摘要", r"概括"],
        SceneType.CREATIVE_WRITING: [r"写.*文章", r"创作"],
    }

    def classify(self, prompt: str) -> SceneType:
        for scene, patterns in self.PATTERNS.items():
            for p in patterns:
                if re.search(p, prompt):
                    return scene
        return SceneType.COMPLEX_REASONING if len(prompt) > 500 else SceneType.SIMPLE_QA


@dataclass
class ModelConfig:
    name: str
    cost_per_1k: float
    avg_latency_ms: float
    quality_score: float
    status: str = "healthy"


@dataclass
class RoutingRule:
    scene: SceneType
    preferred_models: list[str]
    min_quality: float = 0.5


class ModelRoutingEngine:
    def __init__(self):
        self.models: dict[str, ModelConfig] = {}
        self.rules: dict[SceneType, RoutingRule] = {}
        self.classifier = SceneClassifier()
        self.history: list[dict] = []

    def register_model(self, cfg: ModelConfig):
        self.models[cfg.name] = cfg

    def add_rule(self, rule: RoutingRule):
        self.rules[rule.scene] = rule

    def route(self, prompt: str,
              cost_w=0.3, latency_w=0.3, quality_w=0.4) -> dict:
        scene = self.classifier.classify(prompt)
        rule = self.rules.get(scene)

        candidates = []
        if rule:
            for n in rule.preferred_models:
                m = self.models.get(n)
                if m and m.status == "healthy":
                    candidates.append(m)
        if not candidates:
            candidates = [m for m in self.models.values() if m.status == "healthy"]
        if not candidates:
            return {"error": "no_available_model"}

        scored = []
        for m in candidates:
            cs = 1.0 - min(m.cost_per_1k / 0.02, 1.0)
            ls = 1.0 - min(m.avg_latency_ms / 1000, 1.0)
            qs = m.quality_score
            total = cost_w * cs + latency_w * ls + quality_w * qs
            scored.append((m, round(total, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        sel = scored[0][0]

        result = {
            "model": sel.name, "scene": scene.value,
            "score": scored[0][1],
            "cost": sel.cost_per_1k, "latency": sel.avg_latency_ms,
            "all_scores": [(m.name, s) for m, s in scored],
        }
        self.history.append({**result, "ts": time.time()})
        return result

    def stats(self):
        mc = Counter(h["model"] for h in self.history)
        sc = Counter(h["scene"] for h in self.history)
        return {"total": len(self.history), "by_model": dict(mc), "by_scene": dict(sc)}

    def fail_model(self, name):
        if name in self.models:
            self.models[name].status = "down"

    def recover_model(self, name):
        if name in self.models:
            self.models[name].status = "healthy"


def main():
    engine = ModelRoutingEngine()

    # 注册模型
    engine.register_model(ModelConfig("gpt-4o", 0.015, 350, 0.95))
    engine.register_model(ModelConfig("gpt-4o-mini", 0.0006, 150, 0.75))
    engine.register_model(ModelConfig("claude-3.5", 0.015, 400, 0.93))
    engine.register_model(ModelConfig("llama-3-8b", 0.001, 80, 0.65))

    # 注册路由规则
    engine.add_rule(RoutingRule(SceneType.SIMPLE_QA, ["gpt-4o-mini", "llama-3-8b"]))
    engine.add_rule(RoutingRule(SceneType.COMPLEX_REASONING, ["gpt-4o", "claude-3.5"], min_quality=0.9))
    engine.add_rule(RoutingRule(SceneType.CODE_GENERATION, ["gpt-4o", "claude-3.5"], min_quality=0.9))
    engine.add_rule(RoutingRule(SceneType.SUMMARIZATION, ["gpt-4o-mini", "claude-3.5"]))

    print("=" * 60)
    print("模型路由策略演示")
    print("=" * 60)

    # 1. 不同场景路由
    print("\n--- 1. 场景路由 ---")
    queries = [
        "退货流程是什么？",
        "请帮我写一个Python排序函数的代码",
        "请总结以下文章的核心观点",
        "分析这份合同中的法律风险，考虑多种可能的违约场景和应对策略",
        "配送需要多久？",
        "写一篇关于AI未来的文章",
    ]
    for q in queries:
        r = engine.route(q)
        print(f"  [{r['scene']:22s}] -> {r['model']:15s} "
              f"score={r['score']} cost=${r['cost']}")

    # 2. 权重调整
    print("\n--- 2. 权重调整效果 ---")
    test_q = "退货流程是什么？"
    configs = [
        ("均衡", 0.33, 0.33, 0.34),
        ("成本优先", 0.7, 0.1, 0.2),
        ("质量优先", 0.1, 0.1, 0.8),
        ("延迟优先", 0.1, 0.7, 0.2),
    ]
    for label, cw, lw, qw in configs:
        r = engine.route(test_q, cost_w=cw, latency_w=lw, quality_w=qw)
        print(f"  [{label:8s}] -> {r['model']:15s} score={r['score']}")

    # 3. 故障降级
    print("\n--- 3. 故障降级 ---")
    print(f"  模拟gpt-4o-mini故障...")
    engine.fail_model("gpt-4o-mini")
    r = engine.route("退货流程是什么？")
    print(f"  简单FAQ降级到: {r['model']}")

    engine.fail_model("llama-3-8b")
    r = engine.route("退货流程是什么？")
    print(f"  再故障后降级到: {r['model']}")

    engine.recover_model("gpt-4o-mini")
    engine.recover_model("llama-3-8b")
    print(f"  恢复后...")
    r = engine.route("退货流程是什么？")
    print(f"  恢复路由到: {r['model']}")

    # 4. 路由统计
    print("\n--- 4. 路由统计 ---")
    stats = engine.stats()
    print(f"  总调用: {stats['total']}")
    print(f"  按模型: {stats['by_model']}")
    print(f"  按场景: {stats['by_scene']}")


if __name__ == "__main__":
    main()
