"""
AI A/B测试框架演示
对应文章：57-AB测试Prompt版本RAG策略如何科学对比
"""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field


@dataclass
class Variant:
    name: str
    description: str
    config: dict = field(default_factory=dict)
    weight: float = 0.5


@dataclass
class ExperimentResult:
    variant: str
    user_id: str
    metrics: dict = field(default_factory=dict)


class ABTestFramework:
    def __init__(self, name: str, variants: list[Variant]):
        self.name = name
        self.variants = {v.name: v for v in variants}
        self.results: list[ExperimentResult] = []

    def assign(self, user_id: str) -> str:
        h = int(hashlib.md5(
            f"{self.name}:{user_id}".encode()
        ).hexdigest(), 16)
        ratio = (h % 10000) / 10000.0
        cumulative = 0.0
        for name, v in self.variants.items():
            cumulative += v.weight
            if ratio < cumulative:
                return name
        return list(self.variants.keys())[-1]

    def record(self, result: ExperimentResult):
        self.results.append(result)

    def analyze(self) -> dict:
        by_var: dict[str, list[ExperimentResult]] = {}
        for r in self.results:
            by_var.setdefault(r.variant, []).append(r)

        analysis = {}
        for name, results in by_var.items():
            agg = self._agg(results)
            analysis[name] = {"n": len(results), "metrics": agg}

        names = list(analysis.keys())
        if len(names) == 2:
            a, b = names
            for metric in analysis[a]["metrics"]:
                sig = self._z_test(by_var[a], by_var[b], metric)
                analysis[f"sig_{metric}"] = sig
        return analysis

    @staticmethod
    def _agg(results: list[ExperimentResult]) -> dict:
        all_m: dict[str, list] = {}
        for r in results:
            for k, v in r.metrics.items():
                all_m.setdefault(k, []).append(v)
        return {k: round(sum(v) / len(v), 4) for k, v in all_m.items()}

    @staticmethod
    def _z_test(ga: list[ExperimentResult],
                gb: list[ExperimentResult], metric: str) -> dict:
        va = [r.metrics.get(metric, 0) for r in ga]
        vb = [r.metrics.get(metric, 0) for r in gb]
        na, nb = len(va), len(vb)
        if na < 2 or nb < 2:
            return {"significant": False, "reason": "样本不足"}
        ma = sum(va) / na
        mb = sum(vb) / nb
        sa = sum((x - ma) ** 2 for x in va) / (na - 1)
        sb = sum((x - mb) ** 2 for x in vb) / (nb - 1)
        se = math.sqrt(sa / na + sb / nb) if (sa + sb) > 0 else 1
        z = (ma - mb) / se if se > 0 else 0
        return {
            "mean_a": round(ma, 4), "mean_b": round(mb, 4),
            "z": round(z, 4), "significant": abs(z) > 1.96,
            "lift_pct": round((ma - mb) / mb * 100, 2) if mb else 0,
        }


def calc_sample_size(baseline: float, mde: float) -> int:
    z_a, z_b = 1.96, 0.84
    p1, p2 = baseline, baseline + mde
    pa = (p1 + p2) / 2
    n = ((z_a * math.sqrt(2 * pa * (1 - pa)) +
          z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (mde ** 2)
    return int(math.ceil(n))


if __name__ == "__main__":
    print("=" * 60)
    print("AI A/B测试框架演示")
    print("=" * 60)

    # 创建实验: 对比两个Prompt版本
    ab = ABTestFramework("prompt-v2-test", [
        Variant("control", "当前Prompt v1", weight=0.5),
        Variant("treatment", "优化Prompt v2", weight=0.5),
    ])

    # 模拟500个用户
    for i in range(500):
        uid = f"user-{i:04d}"
        variant = ab.assign(uid)
        # 模拟指标: treatment略好
        base_adopt = 0.70 if variant == "control" else 0.75
        base_hall = 0.05 if variant == "control" else 0.03
        ab.record(ExperimentResult(
            variant=variant, user_id=uid,
            metrics={
                "adoption_rate": 1.0 if random.random() < base_adopt else 0.0,
                "hallucination": 1.0 if random.random() < base_hall else 0.0,
                "cost_usd": random.uniform(0.005, 0.02),
            },
        ))

    # 分析结果
    result = ab.analyze()
    print("\n📊 实验结果:")
    for k, v in result.items():
        if isinstance(v, dict):
            print(f"\n  {k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")

    # 样本量计算
    print(f"\n{'='*60}")
    print("📐 样本量计算:")
    for mde in [0.03, 0.05, 0.10]:
        n = calc_sample_size(baseline=0.70, mde=mde)
        print(f"  基线70%, 检测{mde:.0%}差异 → 每组需 {n} 样本")
