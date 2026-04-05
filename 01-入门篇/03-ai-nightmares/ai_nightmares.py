"""
AI工程师的四大噩梦：幻觉、延迟、成本、评估
——监控、检测与治理工具集

配套文章：《AI工程师的四大噩梦：幻觉、延迟、成本、评估》
"""

import time
import random


# ============================================================
# 1. 幻觉检测：引用-答案一致性校验
# ============================================================

class HallucinationDetector:
    """三段式幻觉防线：检索层 → 生成层 → 校验层"""

    def __init__(self, faithfulness_threshold=0.8):
        self.threshold = faithfulness_threshold

    def check(self, answer_text, citations, source_docs):
        """
        检查答案是否存在幻觉
        - answer_text: 模型生成的答案
        - citations: 答案中声称的引用
        - source_docs: 实际检索到的文档内容
        """
        # 第一关：是否有引用
        if not citations:
            return {"status": "risky", "reason": "无引用来源", "score": 0.0}

        # 第二关：引用-答案一致性（简化版：关键词重叠度）
        faithfulness = self._compute_faithfulness(answer_text, source_docs)
        if faithfulness < self.threshold:
            return {
                "status": "risky",
                "reason": f"忠实度 {faithfulness:.2f} 低于阈值 {self.threshold}",
                "score": faithfulness,
            }

        # 第三关：通过校验
        return {"status": "safe", "score": faithfulness}

    def _compute_faithfulness(self, answer, docs):
        """简化的忠实度计算：答案字符片段在文档中的覆盖率（支持中文）"""
        doc_text = " ".join(docs).lower()
        # 使用字符级n-gram（bigram）做覆盖率估算，兼容中英文
        n = 2
        answer_clean = answer.lower().replace(" ", "")
        if len(answer_clean) < n:
            return 1.0 if answer_clean in doc_text.replace(" ", "") else 0.0

        answer_ngrams = [answer_clean[i:i+n] for i in range(len(answer_clean) - n + 1)]
        doc_clean = doc_text.replace(" ", "")
        matched = sum(1 for ng in answer_ngrams if ng in doc_clean)
        return matched / len(answer_ngrams) if answer_ngrams else 0.0


# ============================================================
# 2. 延迟追踪：P50/P95/P99 分位数监控
# ============================================================

class LatencyTracker:
    """延迟分位数追踪器，关注P95而非平均值"""

    def __init__(self):
        self.records = []

    def record(self, latency_ms):
        """记录一次请求的延迟（毫秒）"""
        self.records.append(latency_ms)

    def report(self):
        """生成延迟报告"""
        if not self.records:
            return {"p50": 0, "p95": 0, "p99": 0, "avg": 0, "count": 0}

        sorted_r = sorted(self.records)
        n = len(sorted_r)
        return {
            "p50": sorted_r[int(n * 0.50)],
            "p95": sorted_r[int(n * 0.95)] if n > 1 else sorted_r[-1],
            "p99": sorted_r[int(n * 0.99)] if n > 1 else sorted_r[-1],
            "avg": round(sum(sorted_r) / n, 1),
            "count": n,
        }

    def check_slo(self, p95_target_ms=3000):
        """检查是否满足SLO"""
        report = self.report()
        return {
            "meets_slo": report["p95"] <= p95_target_ms,
            "p95": report["p95"],
            "target": p95_target_ms,
        }


# ============================================================
# 3. 成本控制：请求级 + 用户级双重预算闸门
# ============================================================

class TokenBudgetGate:
    """Token预算闸门：防止成本失控"""

    def __init__(self, max_tokens_per_request=4000, daily_limit_per_user=50000):
        self.max_per_request = max_tokens_per_request
        self.daily_limit = daily_limit_per_user
        self.user_usage = {}

    def check(self, user_id, estimated_tokens):
        """检查请求是否在预算内"""
        # 请求级检查
        if estimated_tokens > self.max_per_request:
            return {
                "allowed": False,
                "reason": f"单次请求Token({estimated_tokens})超限({self.max_per_request})",
            }

        # 用户级检查
        used = self.user_usage.get(user_id, 0)
        if used + estimated_tokens > self.daily_limit:
            return {
                "allowed": False,
                "reason": f"用户日配额已用尽(已用{used}/{self.daily_limit})",
            }

        return {
            "allowed": True,
            "remaining": self.daily_limit - used - estimated_tokens,
        }

    def record_usage(self, user_id, tokens_used):
        """记录实际Token消耗"""
        self.user_usage[user_id] = self.user_usage.get(user_id, 0) + tokens_used

    def get_cost_report(self, price_per_token=0.00003):
        """生成成本报告"""
        report = {}
        for user_id, tokens in self.user_usage.items():
            report[user_id] = {
                "tokens": tokens,
                "cost_usd": round(tokens * price_per_token, 4),
            }
        return report


# ============================================================
# 4. 评估门禁：发布前自动化评估
# ============================================================

class ReleaseGate:
    """发布门禁：三关都过才能上线"""

    def __init__(self, min_faithfulness=0.85, min_adoption=0.60, regression_tolerance=0.05):
        self.min_faithfulness = min_faithfulness
        self.min_adoption = min_adoption
        self.regression_tolerance = regression_tolerance

    def evaluate(self, eval_results, baseline=None):
        """
        评估是否可以发布
        - eval_results: {"faithfulness": 0.9, "adoption_rate": 0.7, "score": 8.2}
        - baseline: 上一版本的指标（用于回归检测）
        """
        gates = {}

        # 门禁1：忠实度达标
        gates["faithfulness"] = {
            "passed": eval_results.get("faithfulness", 0) >= self.min_faithfulness,
            "value": eval_results.get("faithfulness", 0),
            "threshold": self.min_faithfulness,
        }

        # 门禁2：无回归（相对上一版本）
        if baseline:
            current_score = eval_results.get("score", 0)
            baseline_score = baseline.get("score", 0)
            no_regression = current_score >= baseline_score * (1 - self.regression_tolerance)
            gates["no_regression"] = {
                "passed": no_regression,
                "current": current_score,
                "baseline": baseline_score,
            }
        else:
            gates["no_regression"] = {"passed": True, "note": "无基线，跳过回归检测"}

        # 门禁3：采纳率达标
        gates["adoption_rate"] = {
            "passed": eval_results.get("adoption_rate", 0) >= self.min_adoption,
            "value": eval_results.get("adoption_rate", 0),
            "threshold": self.min_adoption,
        }

        all_passed = all(g["passed"] for g in gates.values())
        return {"passed": all_passed, "gates": gates}


# ============================================================
# 演示：四大噩梦治理工具实战
# ============================================================

def main():
    print("=== AI四大噩梦治理工具演示 ===\n")

    # --- 1. 幻觉检测 ---
    print("--- 1. 幻觉检测 ---")
    detector = HallucinationDetector(faithfulness_threshold=0.5)
    result = detector.check(
        answer_text="退货流程需要先申请退货 然后寄回商品 收到后退款",
        citations=["退货政策文档"],
        source_docs=["退货流程 先申请退货 寄回商品 收到后退款 七天无理由"],
    )
    print(f"检测结果: {result['status']} (忠实度: {result['score']:.2f})")

    # 测试无引用的情况
    result2 = detector.check(
        answer_text="这个产品非常好用",
        citations=[],
        source_docs=["产品说明书"],
    )
    print(f"无引用检测: {result2['status']} ({result2['reason']})")

    # --- 2. 延迟追踪 ---
    print("\n--- 2. 延迟追踪 ---")
    tracker = LatencyTracker()
    # 模拟100次请求的延迟数据
    random.seed(42)
    for _ in range(100):
        # 大部分请求100-300ms，少量长尾请求500-2000ms
        if random.random() < 0.9:
            latency = random.randint(80, 350)
        else:
            latency = random.randint(500, 2000)
        tracker.record(latency)

    report = tracker.report()
    print(f"延迟报告: P50={report['p50']}ms, P95={report['p95']}ms, P99={report['p99']}ms")
    slo = tracker.check_slo(p95_target_ms=1000)
    print(f"SLO检查: {'达标' if slo['meets_slo'] else '未达标'} (P95={slo['p95']}ms, 目标<{slo['target']}ms)")

    # --- 3. 成本控制 ---
    print("\n--- 3. 成本控制 ---")
    gate = TokenBudgetGate(max_tokens_per_request=4000, daily_limit_per_user=50000)

    # 正常请求
    check1 = gate.check("user_001", 2000)
    print(f"正常请求: allowed={check1['allowed']}, remaining={check1.get('remaining')}")
    gate.record_usage("user_001", 2000)

    # 模拟大量使用后超限
    gate.record_usage("user_001", 48000)
    check2 = gate.check("user_001", 1000)
    print(f"超限请求: allowed={check2['allowed']}, reason={check2.get('reason')}")

    # 成本报告
    cost_report = gate.get_cost_report()
    print(f"成本报告: {cost_report}")

    # --- 4. 评估门禁 ---
    print("\n--- 4. 评估门禁 ---")
    release_gate = ReleaseGate()

    # 通过的情况
    result_pass = release_gate.evaluate(
        eval_results={"faithfulness": 0.92, "adoption_rate": 0.75, "score": 8.5},
        baseline={"score": 8.2},
    )
    print(f"门禁结果: passed={result_pass['passed']}")
    for name, detail in result_pass["gates"].items():
        status = "✅" if detail["passed"] else "❌"
        print(f"  {status} {name}: {detail}")

    # 未通过的情况
    print()
    result_fail = release_gate.evaluate(
        eval_results={"faithfulness": 0.70, "adoption_rate": 0.45, "score": 6.0},
        baseline={"score": 8.2},
    )
    print(f"门禁结果: passed={result_fail['passed']}")
    for name, detail in result_fail["gates"].items():
        status = "✅" if detail["passed"] else "❌"
        print(f"  {status} {name}: {detail}")


if __name__ == "__main__":
    main()
