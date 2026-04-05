"""
系统提示词的企业级管理：版本化、A/B测试、灰度发布

演示内容：
1. Prompt版本管理（注册、激活、回滚）
2. A/B测试路由（基于用户ID哈希的流量分流）
3. 灰度发布（金丝雀发布 + 逐步扩量）

运行: python prompt_management_demo.py
依赖: 无（纯标准库）
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import hashlib
import random


# ============================================================
# 1. Prompt版本模型
# ============================================================

class PromptStatus(str, Enum):
    DRAFT = "draft"
    TESTING = "testing"
    CANARY = "canary"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class PromptVersion:
    """Prompt版本数据模型"""
    prompt_id: str
    version: str
    content: str
    status: PromptStatus = PromptStatus.DRAFT
    author: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                self.content.encode()
            ).hexdigest()[:12]

    def __repr__(self):
        return f"{self.prompt_id} / {self.version} [{self.status.value}]"


# ============================================================
# 2. 版本管理器
# ============================================================

class PromptVersionManager:
    """Prompt版本管理——注册、激活、回滚、查询"""

    def __init__(self):
        self._versions: dict[str, list[PromptVersion]] = {}
        self._active: dict[str, PromptVersion] = {}

    def register(self, prompt: PromptVersion) -> None:
        if prompt.prompt_id not in self._versions:
            self._versions[prompt.prompt_id] = []
        self._versions[prompt.prompt_id].append(prompt)

    def activate(self, prompt_id: str, version: str) -> bool:
        for pv in self._versions.get(prompt_id, []):
            if pv.version == version:
                if prompt_id in self._active:
                    self._active[prompt_id].status = PromptStatus.ARCHIVED
                pv.status = PromptStatus.ACTIVE
                self._active[prompt_id] = pv
                return True
        return False

    def rollback(self, prompt_id: str) -> Optional[PromptVersion]:
        versions = self._versions.get(prompt_id, [])
        archived = [v for v in versions if v.status == PromptStatus.ARCHIVED]
        if not archived:
            return None
        prev = archived[-1]
        self.activate(prompt_id, prev.version)
        return prev

    def get_active(self, prompt_id: str) -> Optional[PromptVersion]:
        return self._active.get(prompt_id)

    def get_history(self, prompt_id: str) -> list[PromptVersion]:
        return self._versions.get(prompt_id, [])


# ============================================================
# 3. A/B测试路由器
# ============================================================

class ABTestRouter:
    """基于用户ID哈希的A/B测试流量路由"""

    def __init__(self):
        self._experiments: dict[str, dict] = {}

    def create_experiment(
        self,
        experiment_id: str,
        control: PromptVersion,
        treatment: PromptVersion,
        traffic_ratio: float = 0.5,
    ):
        self._experiments[experiment_id] = {
            "control": control,
            "treatment": treatment,
            "ratio": traffic_ratio,
            "metrics": {"control": [], "treatment": []},
        }

    def route(self, experiment_id: str, user_id: str) -> PromptVersion:
        exp = self._experiments[experiment_id]
        bucket = self._hash_bucket(user_id)
        if bucket < exp["ratio"]:
            return exp["treatment"]
        return exp["control"]

    def record_metric(self, experiment_id: str, user_id: str, score: float):
        exp = self._experiments[experiment_id]
        bucket = self._hash_bucket(user_id)
        group = "treatment" if bucket < exp["ratio"] else "control"
        exp["metrics"][group].append(score)

    def get_results(self, experiment_id: str) -> dict:
        exp = self._experiments[experiment_id]
        results = {}
        for group in ["control", "treatment"]:
            scores = exp["metrics"][group]
            results[group] = {
                "samples": len(scores),
                "avg_score": round(sum(scores) / len(scores), 3) if scores else 0,
            }
        return results

    @staticmethod
    def _hash_bucket(user_id: str) -> float:
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_val % 100) / 100.0


# ============================================================
# 4. 灰度发布控制器
# ============================================================

class CanaryDeployer:
    """金丝雀发布——逐步扩量 + 异常回滚"""

    def __init__(self, manager: PromptVersionManager):
        self.manager = manager
        self._canary: dict[str, dict] = {}

    def start_canary(
        self, prompt_id: str, new_version: str, initial_ratio: float = 0.05
    ):
        self._canary[prompt_id] = {
            "new_version": new_version,
            "ratio": initial_ratio,
        }

    def resolve_prompt(self, prompt_id: str, user_id: str) -> PromptVersion:
        if prompt_id not in self._canary:
            return self.manager.get_active(prompt_id)

        canary = self._canary[prompt_id]
        bucket = ABTestRouter._hash_bucket(user_id)

        if bucket < canary["ratio"]:
            for v in self.manager.get_history(prompt_id):
                if v.version == canary["new_version"]:
                    return v
        return self.manager.get_active(prompt_id)

    def expand_ratio(self, prompt_id: str, new_ratio: float):
        if prompt_id in self._canary:
            self._canary[prompt_id]["ratio"] = min(new_ratio, 1.0)

    def finish_canary(self, prompt_id: str, promote: bool = True):
        if prompt_id not in self._canary:
            return
        canary = self._canary.pop(prompt_id)
        if promote:
            self.manager.activate(prompt_id, canary["new_version"])


# ============================================================
# 5. 演示主流程
# ============================================================

def demo_version_management():
    print("=" * 50)
    print("=== Prompt版本管理演示 ===")
    print("=" * 50)

    manager = PromptVersionManager()

    v1 = PromptVersion(
        prompt_id="customer_service",
        version="1.0.0",
        content="你是专业的客服助手，请用简洁专业的语气回复用户问题。",
        author="张三",
        description="初始版本",
    )
    v2 = PromptVersion(
        prompt_id="customer_service",
        version="1.1.0",
        content="你是专业的客服助手，请用简洁专业的语气回复用户问题。"
                "回复时先确认用户意图，再给出解决方案。",
        author="李四",
        description="增加意图确认步骤",
    )

    manager.register(v1)
    manager.register(v2)
    print(f"注册版本: {v1.version} (hash={v1.content_hash})")
    print(f"注册版本: {v2.version} (hash={v2.content_hash})")

    manager.activate("customer_service", "1.0.0")
    print(f"激活: {manager.get_active('customer_service')}")

    manager.activate("customer_service", "1.1.0")
    print(f"升级到: {manager.get_active('customer_service')}")

    manager.rollback("customer_service")
    print(f"回滚后: {manager.get_active('customer_service')}")

    return manager, v1, v2


def demo_ab_testing(v1: PromptVersion, v2: PromptVersion):
    print()
    print("=" * 50)
    print("=== A/B测试演示 ===")
    print("=" * 50)

    router = ABTestRouter()
    router.create_experiment("exp_001", control=v1, treatment=v2, traffic_ratio=0.5)

    # 模拟100个用户的路由分布
    control_count = 0
    treatment_count = 0
    for i in range(100):
        user_id = f"user_{i:03d}"
        result = router.route("exp_001", user_id)
        if result.version == v1.version:
            control_count += 1
        else:
            treatment_count += 1

    print(f"100个用户分流: control={control_count}, treatment={treatment_count}")

    # 模拟指标采集
    random.seed(42)
    for i in range(200):
        user_id = f"user_{i:03d}"
        prompt = router.route("exp_001", user_id)
        # 模拟: treatment版本效果略好
        base_score = 0.75 if prompt.version == v2.version else 0.70
        score = base_score + random.uniform(-0.15, 0.15)
        router.record_metric("exp_001", user_id, score)

    results = router.get_results("exp_001")
    print(f"实验结果:")
    print(f"  control  (v{v1.version}): {results['control']}")
    print(f"  treatment(v{v2.version}): {results['treatment']}")


def demo_canary_deploy(manager: PromptVersionManager):
    print()
    print("=" * 50)
    print("=== 灰度发布演示 ===")
    print("=" * 50)

    deployer = CanaryDeployer(manager)

    # 确保v1是当前激活版本
    manager.activate("customer_service", "1.0.0")
    print(f"当前版本: {manager.get_active('customer_service')}")

    # 启动灰度: v1.1.0 先接5%流量
    deployer.start_canary("customer_service", "1.1.0", initial_ratio=0.05)
    print("启动灰度: v1.1.0 接入5%流量")

    # 模拟用户请求
    hit_new = sum(
        1 for i in range(1000)
        if deployer.resolve_prompt("customer_service", f"user_{i:04d}").version == "1.1.0"
    )
    print(f"  1000个请求中命中新版本: {hit_new} ({hit_new/10:.1f}%)")

    # 扩量到30%
    deployer.expand_ratio("customer_service", 0.30)
    print("扩量到30%")
    hit_new = sum(
        1 for i in range(1000)
        if deployer.resolve_prompt("customer_service", f"user_{i:04d}").version == "1.1.0"
    )
    print(f"  1000个请求中命中新版本: {hit_new} ({hit_new/10:.1f}%)")

    # 全量发布
    deployer.finish_canary("customer_service", promote=True)
    print(f"全量发布完成: {manager.get_active('customer_service')}")


if __name__ == "__main__":
    manager, v1, v2 = demo_version_management()
    demo_ab_testing(v1, v2)
    demo_canary_deploy(manager)
    print()
    print("✅ 演示完成！")
