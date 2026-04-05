"""
LLM评测平台演示：测试集 + 评估引擎 + 发布门禁 + 回归对比
对应文章：73-LLM评测平台离线评估加在线监控加回归测试
"""
from __future__ import annotations

import time
import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class TestCase:
    case_id: str
    question: str
    expected_keywords: list[str]
    forbidden_keywords: list[str] = field(default_factory=list)
    max_tokens: int = 300
    category: str = "general"


@dataclass
class TestSuite:
    suite_id: str
    name: str
    cases: list[TestCase]


@dataclass
class EvalResult:
    case_id: str
    question: str
    response: str
    tokens: int
    keyword_score: float
    safety_passed: bool
    token_efficient: bool
    overall_passed: bool


class EvalEngine:
    def evaluate(self, suite: TestSuite, model_fn) -> dict:
        results = []
        for tc in suite.cases:
            resp, tokens = model_fn(tc.question)
            r = self._eval_case(tc, resp, tokens)
            results.append(r)

        passed = sum(1 for r in results if r.overall_passed)
        total = len(results)
        avg_tok = sum(r.tokens for r in results) / max(total, 1)

        return {
            "suite": suite.name, "total": total, "passed": passed,
            "pass_rate": round(passed / max(total, 1) * 100, 1),
            "avg_tokens": round(avg_tok, 1),
            "details": [
                {"case_id": r.case_id, "question": r.question[:40],
                 "tokens": r.tokens, "kw_score": r.keyword_score,
                 "safety": r.safety_passed, "efficient": r.token_efficient,
                 "passed": r.overall_passed}
                for r in results
            ],
        }

    def _eval_case(self, tc, resp, tokens):
        hits = sum(1 for kw in tc.expected_keywords if kw in resp)
        kw_score = hits / max(len(tc.expected_keywords), 1)
        safety = not any(fw in resp for fw in tc.forbidden_keywords)
        efficient = tokens <= tc.max_tokens
        overall = kw_score >= 0.5 and safety and efficient
        return EvalResult(tc.case_id, tc.question, resp, tokens,
                          round(kw_score, 2), safety, efficient, overall)


class ReleaseGate:
    def __init__(self, min_pass=85.0, max_regression=5.0):
        self.min_pass = min_pass
        self.max_regression = max_regression

    def check(self, report, baseline=None):
        pr = report["pass_rate"]
        gate_ok = pr >= self.min_pass
        reg_ok = True
        reg_rate = 0.0
        if baseline:
            reg_rate = max(0, baseline["pass_rate"] - pr)
            reg_ok = reg_rate <= self.max_regression
        verdict = "✅ 允许发布" if (gate_ok and reg_ok) else "❌ 阻断发布"
        return {
            "verdict": verdict, "pass_rate": pr,
            "min_required": self.min_pass,
            "regression": reg_rate, "max_regression": self.max_regression,
        }


class RegressionComparator:
    def compare(self, old_report, new_report):
        old_d = {d["case_id"]: d for d in old_report.get("details", [])}
        new_d = {d["case_id"]: d for d in new_report.get("details", [])}
        regressions, improvements = [], []
        for cid, nd in new_d.items():
            od = old_d.get(cid)
            if od:
                if od["passed"] and not nd["passed"]:
                    regressions.append(cid)
                elif not od["passed"] and nd["passed"]:
                    improvements.append(cid)
        return {
            "old_rate": old_report["pass_rate"],
            "new_rate": new_report["pass_rate"],
            "regressions": len(regressions),
            "improvements": len(improvements),
            "regressed_cases": regressions,
        }


def make_model(quality=0.8):
    """创建模拟模型函数，quality控制回答质量"""
    def model_fn(question):
        tokens = random.randint(50, 250)
        # 根据quality决定是否包含关键词
        if random.random() < quality:
            resp = f"关于{question}的回答：退货 配送 申请 流程 步骤 产品 功能 请假 年假"
        else:
            resp = f"这是一个无关的回答，不包含任何有用信息。"
        return resp, tokens
    return model_fn


def main():
    engine = EvalEngine()
    gate = ReleaseGate(min_pass=80.0, max_regression=10.0)
    comparator = RegressionComparator()

    print("=" * 60)
    print("LLM评测平台演示")
    print("=" * 60)

    # 1. 创建测试集
    suite = TestSuite("s1", "客服评测集", [
        TestCase("c1", "退货流程是什么？", ["退货", "流程", "申请"]),
        TestCase("c2", "配送需要多久？", ["配送", "工作日"]),
        TestCase("c3", "如何修改地址？", ["修改", "地址"]),
        TestCase("c4", "产品有什么功能？", ["产品", "功能"]),
        TestCase("c5", "怎么请假？", ["请假", "申请"]),
        TestCase("c6", "退款多久到账？", ["退货", "退款"], ["脏话"]),
        TestCase("c7", "投诉渠道在哪？", ["投诉", "渠道"]),
        TestCase("c8", "会员权益有哪些？", ["会员", "权益"]),
    ])
    print(f"\n--- 1. 测试集: {suite.name} ({len(suite.cases)}个case) ---")

    # 2. 评估旧版本
    print("\n--- 2. 评估旧版本 (quality=0.85) ---")
    old_model = make_model(quality=0.85)
    old_report = engine.evaluate(suite, old_model)
    print(f"  通过率: {old_report['pass_rate']}% ({old_report['passed']}/{old_report['total']})")
    print(f"  平均Token: {old_report['avg_tokens']}")

    # 3. 评估新版本
    print("\n--- 3. 评估新版本 (quality=0.90) ---")
    new_model = make_model(quality=0.90)
    new_report = engine.evaluate(suite, new_model)
    print(f"  通过率: {new_report['pass_rate']}% ({new_report['passed']}/{new_report['total']})")
    print(f"  平均Token: {new_report['avg_tokens']}")

    # 4. 回归对比
    print("\n--- 4. 回归对比 ---")
    comparison = comparator.compare(old_report, new_report)
    print(f"  旧版通过率: {comparison['old_rate']}%")
    print(f"  新版通过率: {comparison['new_rate']}%")
    print(f"  回归case: {comparison['regressions']}个")
    print(f"  改进case: {comparison['improvements']}个")
    if comparison["regressed_cases"]:
        print(f"  回归详情: {comparison['regressed_cases']}")

    # 5. 发布门禁
    print("\n--- 5. 发布门禁 ---")
    gate_result = gate.check(new_report, old_report)
    print(f"  判定: {gate_result['verdict']}")
    print(f"  通过率: {gate_result['pass_rate']}% (要求≥{gate_result['min_required']}%)")
    print(f"  回归率: {gate_result['regression']}% (允许≤{gate_result['max_regression']}%)")

    # 6. 详细结果
    print("\n--- 6. 新版本详细结果 ---")
    for d in new_report["details"]:
        icon = "✅" if d["passed"] else "❌"
        print(f"  {icon} [{d['case_id']}] {d['question']} "
              f"kw={d['kw_score']} tok={d['tokens']} safe={d['safety']}")


if __name__ == "__main__":
    main()
