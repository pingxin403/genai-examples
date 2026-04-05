"""
模型版本管理演示
对应文章：48-模型版本管理底座模型升级应用会崩吗
"""
from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class ModelVersion:
    """模型版本定义"""
    model_id: str
    version: str
    provider: str
    config: dict = field(default_factory=dict)
    status: str = "staging"
    traffic_weight: float = 0.0
    metrics: dict = field(default_factory=dict)


class ModelVersionRouter:
    """模型版本路由器"""

    def __init__(self):
        self.versions: dict[str, ModelVersion] = {}
        self.rollback_stack: list[str] = []

    def register(self, version: ModelVersion) -> str:
        key = f"{version.model_id}@{version.version}"
        self.versions[key] = version
        return key

    def set_traffic(self, version_key: str, weight: float):
        if version_key in self.versions:
            self.versions[version_key].traffic_weight = weight
            if weight < 1.0:
                self.versions[version_key].status = "canary"
            else:
                self.versions[version_key].status = "production"

    def route(self, model_id: str):
        candidates = [
            v for v in self.versions.values()
            if v.model_id == model_id and v.traffic_weight > 0
        ]
        if not candidates:
            return None
        total = sum(c.traffic_weight for c in candidates)
        r = random.random() * total
        cumulative = 0.0
        for c in candidates:
            cumulative += c.traffic_weight
            if r <= cumulative:
                return c
        return candidates[-1]

    def rollback(self, model_id: str):
        current = [
            v for v in self.versions.values()
            if v.model_id == model_id
            and v.status in ("canary", "production")
        ]
        for v in current:
            v.traffic_weight = 0.0
            v.status = "rollback"
        if self.rollback_stack:
            prev_key = self.rollback_stack.pop()
            if prev_key in self.versions:
                self.versions[prev_key].traffic_weight = 1.0
                self.versions[prev_key].status = "production"
                return prev_key
        return None

    def promote(self, version_key: str):
        v = self.versions.get(version_key)
        if not v:
            return
        for key, ver in self.versions.items():
            if ver.model_id == v.model_id and ver.status == "production":
                self.rollback_stack.append(key)
                ver.status = "archived"
                ver.traffic_weight = 0.0
        v.status = "production"
        v.traffic_weight = 1.0


class RegressionTestSuite:
    """回归测试套件"""

    def __init__(self, test_cases: list[dict]):
        self.test_cases = test_cases

    def run(self, model_fn) -> dict:
        passed = 0
        failed_cases = []
        for tc in self.test_cases:
            result = model_fn(tc["input"])
            ok = all(
                check(result) for check in tc.get("checks", [])
            )
            if ok:
                passed += 1
            else:
                failed_cases.append(tc["input"][:50])
        return {
            "total": len(self.test_cases),
            "passed": passed,
            "pass_rate": round(passed / len(self.test_cases), 3),
            "failed_samples": failed_cases[:5],
        }


if __name__ == "__main__":
    router = ModelVersionRouter()

    # 注册两个版本
    v1_key = router.register(ModelVersion(
        model_id="contract-review",
        version="v1.0",
        provider="openai",
        config={"model": "gpt-4-0613"},
    ))
    v2_key = router.register(ModelVersion(
        model_id="contract-review",
        version="v2.0",
        provider="openai",
        config={"model": "gpt-4-turbo"},
    ))

    # v1全量上线
    router.promote(v1_key)
    print("=== 初始状态 ===")
    for k, v in router.versions.items():
        print(f"  {k}: status={v.status}, weight={v.traffic_weight}")

    # 灰度v2: 10%流量
    router.set_traffic(v1_key, 0.9)
    router.set_traffic(v2_key, 0.1)
    print("\n=== 灰度10% ===")

    # 模拟100次路由
    dist = Counter()
    for _ in range(100):
        routed = router.route("contract-review")
        if routed:
            dist[routed.version] += 1
    print(f"  路由分布: {dict(dist)}")

    # 模拟发现问题，回滚
    print("\n=== 发现异常，执行回滚 ===")
    rolled = router.rollback("contract-review")
    print(f"  回滚到: {rolled}")
    for k, v in router.versions.items():
        print(f"  {k}: status={v.status}, weight={v.traffic_weight}")

    # 回归测试
    print("\n=== 回归测试 ===")
    suite = RegressionTestSuite([
        {"input": "审查合同条款", "checks": [
            lambda r: isinstance(r, str),
            lambda r: len(r) > 10,
        ]},
        {"input": "提取关键日期", "checks": [
            lambda r: isinstance(r, str),
        ]},
        {"input": "风险评估", "checks": [
            lambda r: isinstance(r, str),
            lambda r: len(r) > 5,
        ]},
    ])
    result = suite.run(lambda x: f"模拟回答: {x}的分析结果...")
    print(f"  通过率: {result['pass_rate']*100:.1f}%")
