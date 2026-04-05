"""
Prompt管理平台演示：版本控制 + CI测试 + 灰度发布
对应文章：70-Prompt管理平台提示词的Git加CICD加灰度
"""
from __future__ import annotations

import time
import hashlib
import random
import re
from dataclasses import dataclass, field
from enum import Enum


class PromptStatus(Enum):
    DRAFT = "draft"
    TESTING = "testing"
    CANARY = "canary"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class PromptVersion:
    version_id: str
    prompt_name: str
    template: str
    variables: list[str]
    status: PromptStatus = PromptStatus.DRAFT
    author: str = ""
    created_at: float = field(default_factory=time.time)
    test_results: dict = field(default_factory=dict)
    traffic_percent: float = 0.0


@dataclass
class TestCase:
    input_vars: dict
    expected_keywords: list[str]
    max_tokens: int = 500


class PromptRegistry:
    def __init__(self):
        self.prompts: dict[str, list[PromptVersion]] = {}
        self.active_versions: dict[str, str] = {}

    def create_version(self, name, template, variables, author) -> PromptVersion:
        vid = hashlib.md5(f"{name}{template}{time.time()}".encode()).hexdigest()[:10]
        pv = PromptVersion(vid, name, template, variables, author=author)
        self.prompts.setdefault(name, []).append(pv)
        return pv

    def get_active(self, name):
        vid = self.active_versions.get(name)
        if not vid:
            return None
        for pv in self.prompts.get(name, []):
            if pv.version_id == vid:
                return pv
        return None

    def activate(self, name, version_id):
        for pv in self.prompts.get(name, []):
            if pv.version_id == version_id:
                pv.status = PromptStatus.ACTIVE
                pv.traffic_percent = 100.0
                self.active_versions[name] = version_id
            elif pv.status == PromptStatus.ACTIVE:
                pv.status = PromptStatus.ARCHIVED
                pv.traffic_percent = 0.0

    def rollback(self, name):
        versions = self.prompts.get(name, [])
        archived = [v for v in versions if v.status == PromptStatus.ARCHIVED]
        if archived:
            prev = archived[-1]
            self.activate(name, prev.version_id)
            return prev
        return None


class PromptCIPipeline:
    def __init__(self, registry: PromptRegistry):
        self.registry = registry
        self.test_suites: dict[str, list[TestCase]] = {}

    def add_test_suite(self, prompt_name, cases):
        self.test_suites[prompt_name] = cases

    def run_tests(self, prompt_name, version_id) -> dict:
        pv = None
        for v in self.registry.prompts.get(prompt_name, []):
            if v.version_id == version_id:
                pv = v
                break
        if not pv:
            return {"passed": False, "error": "version_not_found"}

        cases = self.test_suites.get(prompt_name, [])
        if not cases:
            return {"passed": True, "warning": "no_test_cases"}

        results = []
        for i, tc in enumerate(cases):
            rendered = pv.template
            for k, v in tc.input_vars.items():
                rendered = rendered.replace(f"{{{k}}}", v)

            tokens = len(rendered.split()) * 2
            keyword_hits = sum(1 for kw in tc.expected_keywords if kw in rendered)
            passed = keyword_hits > 0 and tokens <= tc.max_tokens

            # 检查未替换变量
            unreplaced = re.findall(r'\{(\w+)\}', rendered)

            results.append({
                "case": i + 1, "passed": passed and not unreplaced,
                "tokens": tokens,
                "keyword_hits": f"{keyword_hits}/{len(tc.expected_keywords)}",
                "unreplaced_vars": unreplaced,
            })

        all_passed = all(r["passed"] for r in results)
        pv.test_results = {"passed": all_passed, "details": results}
        pv.status = PromptStatus.TESTING
        return {"passed": all_passed, "results": results}


class CanaryDeployer:
    def __init__(self, registry: PromptRegistry):
        self.registry = registry
        self.configs: dict[str, dict] = {}

    def start_canary(self, name, new_vid, percent=5.0):
        old_vid = self.registry.active_versions.get(name)
        for v in self.registry.prompts.get(name, []):
            if v.version_id == new_vid:
                v.status = PromptStatus.CANARY
                v.traffic_percent = percent
            elif v.version_id == old_vid:
                v.traffic_percent = 100.0 - percent
        self.configs[name] = {
            "old": old_vid, "new": new_vid, "percent": percent,
        }

    def resolve(self, name) -> str:
        cfg = self.configs.get(name)
        if not cfg:
            return self.registry.active_versions.get(name, "")
        return cfg["new"] if random.random() * 100 < cfg["percent"] else cfg["old"]

    def promote(self, name):
        cfg = self.configs.get(name)
        if cfg:
            self.registry.activate(name, cfg["new"])
            del self.configs[name]

    def rollback_canary(self, name):
        cfg = self.configs.get(name)
        if cfg and cfg["old"]:
            self.registry.activate(name, cfg["old"])
            del self.configs[name]


def main():
    registry = PromptRegistry()
    ci = PromptCIPipeline(registry)
    canary = CanaryDeployer(registry)

    print("=" * 60)
    print("Prompt管理平台演示")
    print("=" * 60)

    # 1. 创建Prompt版本
    print("\n--- 1. 创建Prompt版本 ---")
    v1 = registry.create_version(
        "customer_service",
        "你是客服助手。用户问题：{question}。请用简洁的语言回答。",
        ["question"], "engineer_a",
    )
    print(f"  v1: {v1.version_id} by {v1.author} [{v1.status.value}]")

    v2 = registry.create_version(
        "customer_service",
        "你是专业客服。用户问题：{question}。请分步骤详细解释。",
        ["question"], "engineer_b",
    )
    print(f"  v2: {v2.version_id} by {v2.author} [{v2.status.value}]")

    # 2. CI测试
    print("\n--- 2. CI测试 ---")
    ci.add_test_suite("customer_service", [
        TestCase({"question": "退货流程"}, ["客服", "问题"], max_tokens=200),
        TestCase({"question": "配送时间"}, ["客服", "问题"], max_tokens=200),
    ])

    for v in [v1, v2]:
        result = ci.run_tests("customer_service", v.version_id)
        status = "✅ 通过" if result["passed"] else "❌ 失败"
        print(f"  {v.version_id}: {status}")
        if result.get("results"):
            for r in result["results"]:
                print(f"    Case {r['case']}: passed={r['passed']} tokens={r['tokens']}")

    # 3. 激活v1
    print("\n--- 3. 激活v1 ---")
    registry.activate("customer_service", v1.version_id)
    active = registry.get_active("customer_service")
    print(f"  当前活跃: {active.version_id} [{active.status.value}]")

    # 4. 灰度发布v2
    print("\n--- 4. 灰度发布v2 (10%流量) ---")
    canary.start_canary("customer_service", v2.version_id, percent=10.0)
    counts = {"v1": 0, "v2": 0}
    for _ in range(100):
        vid = canary.resolve("customer_service")
        if vid == v1.version_id:
            counts["v1"] += 1
        else:
            counts["v2"] += 1
    print(f"  100次请求分配: v1={counts['v1']}次 v2={counts['v2']}次")

    # 5. 全量发布
    print("\n--- 5. 全量发布v2 ---")
    canary.promote("customer_service")
    active = registry.get_active("customer_service")
    print(f"  当前活跃: {active.version_id} [{active.status.value}]")

    # 6. 回滚
    print("\n--- 6. 回滚到上一版本 ---")
    prev = registry.rollback("customer_service")
    if prev:
        print(f"  回滚到: {prev.version_id} [{prev.status.value}]")

    # 7. 版本历史
    print("\n--- 7. 版本历史 ---")
    for v in registry.prompts.get("customer_service", []):
        print(f"  {v.version_id} | {v.status.value:10s} | {v.author} | {v.template[:40]}...")


if __name__ == "__main__":
    main()
