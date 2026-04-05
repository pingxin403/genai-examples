"""
从Demo到线上的5步生产就绪检查清单
对应文章：🧪《我的第一个AI项目复盘：从Demo到线上只差这5步》

演示内容：
1. 生产就绪评估器 - 量化AI系统质量
2. Prompt加固器 - 处理边界情况
3. 生产环境防护 - 限流/成本/缓存
4. AI可观测性 - 日志/指标/告警
5. 灰度发布 - 小步快跑
"""

import time
import random
from datetime import datetime
from collections import defaultdict


# ============================================================
# Step 1: 生产就绪评估器
# ============================================================

class ProductionReadinessEvaluator:
    """生产就绪评估器：量化AI系统的各项指标"""

    def __init__(self):
        self.test_cases = []
        self.results = []

    def add_test_case(self, question, expected_keywords, forbidden_keywords=None):
        self.test_cases.append({
            "question": question,
            "expected_keywords": expected_keywords,
            "forbidden_keywords": forbidden_keywords or [],
        })

    def evaluate_response(self, response, expected_keywords, forbidden_keywords):
        hits = sum(1 for kw in expected_keywords if kw in response)
        keyword_score = hits / len(expected_keywords) if expected_keywords else 0

        violations = [kw for kw in forbidden_keywords if kw in response]
        safety_score = 1.0 if not violations else 0.0

        length = len(response)
        if length < 20:
            length_score = 0.3
        elif length > 1000:
            length_score = 0.6
        else:
            length_score = 1.0

        return {
            "keyword_score": round(keyword_score, 2),
            "safety_score": safety_score,
            "length_score": length_score,
            "violations": violations,
            "overall": round(keyword_score * 0.5 + safety_score * 0.3 + length_score * 0.2, 2),
        }

    def run_evaluation(self, ai_fn):
        """对所有测试用例运行评估"""
        self.results = []
        for case in self.test_cases:
            response = ai_fn(case["question"])
            result = self.evaluate_response(
                response, case["expected_keywords"], case["forbidden_keywords"]
            )
            result["question"] = case["question"]
            result["response"] = response[:80] + "..." if len(response) > 80 else response
            self.results.append(result)
        return self.results

    def summary(self):
        if not self.results:
            return "未运行评估"
        avg_score = sum(r["overall"] for r in self.results) / len(self.results)
        pass_count = sum(1 for r in self.results if r["overall"] >= 0.7)
        return {
            "total": len(self.results),
            "passed": pass_count,
            "avg_score": round(avg_score, 2),
            "pass_rate": f"{pass_count / len(self.results):.0%}",
        }


# ============================================================
# Step 2: Prompt加固器
# ============================================================

class PromptHardener:
    """Prompt加固器：处理边界情况和异常输入"""

    def __init__(self, base_prompt):
        self.base_prompt = base_prompt
        self.guardrails = []

    def add_guardrail(self, name, check_fn, fallback_response):
        self.guardrails.append({
            "name": name,
            "check": check_fn,
            "fallback": fallback_response,
        })

    def process(self, user_input):
        for rail in self.guardrails:
            if rail["check"](user_input):
                return {"blocked": True, "reason": rail["name"], "response": rail["fallback"]}
        return {"blocked": False, "prompt": self.base_prompt + "\n用户问题：" + user_input}


# ============================================================
# Step 3: 生产环境防护
# ============================================================

class ProductionGuard:
    """生产环境防护：限流 + 成本控制 + 缓存"""

    def __init__(self, max_qps=50, daily_token_budget=500000):
        self.max_qps = max_qps
        self.daily_token_budget = daily_token_budget
        self.request_timestamps = []
        self.daily_token_usage = 0
        self.cache = {}
        self.metrics = defaultdict(int)

    def check_rate_limit(self):
        now = time.time()
        self.request_timestamps = [t for t in self.request_timestamps if now - t < 1.0]
        if len(self.request_timestamps) >= self.max_qps:
            self.metrics["rate_limited"] += 1
            return False
        self.request_timestamps.append(now)
        return True

    def check_budget(self, estimated_tokens):
        if self.daily_token_usage + estimated_tokens > self.daily_token_budget:
            self.metrics["budget_exceeded"] += 1
            return False
        return True

    def try_cache(self, question):
        if question in self.cache:
            self.metrics["cache_hits"] += 1
            return self.cache[question]
        self.metrics["cache_misses"] += 1
        return None

    def record_usage(self, question, response, tokens_used):
        self.daily_token_usage += tokens_used
        self.cache[question] = response
        self.metrics["total_requests"] += 1
        self.metrics["total_tokens"] += tokens_used

    def get_status(self):
        return {
            "daily_token_usage": self.daily_token_usage,
            "budget_remaining": self.daily_token_budget - self.daily_token_usage,
            "cache_size": len(self.cache),
            "metrics": dict(self.metrics),
        }


# ============================================================
# Step 4: AI可观测性
# ============================================================

class AIObservability:
    """AI可观测性：日志 + 指标 + 告警"""

    def __init__(self):
        self.logs = []
        self.metrics = {
            "total_requests": 0,
            "hallucination_count": 0,
            "avg_latency_ms": 0,
            "total_tokens": 0,
        }
        self._latencies = []

    def log_request(self, question, response, latency_ms, tokens, confidence):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question[:50],
            "response_length": len(response),
            "latency_ms": latency_ms,
            "tokens": tokens,
            "confidence": confidence,
        }
        self.logs.append(entry)
        self._update_metrics(latency_ms, tokens)

    def _update_metrics(self, latency_ms, tokens):
        self.metrics["total_requests"] += 1
        self.metrics["total_tokens"] += tokens
        self._latencies.append(latency_ms)
        self.metrics["avg_latency_ms"] = round(
            sum(self._latencies) / len(self._latencies), 1
        )

    def report_hallucination(self):
        self.metrics["hallucination_count"] += 1

    def check_alerts(self):
        triggered = []
        total = self.metrics["total_requests"]
        if total > 0:
            hallucination_rate = self.metrics["hallucination_count"] / total
            if hallucination_rate > 0.05:
                triggered.append(f"幻觉率告警: {hallucination_rate:.1%} > 5%")
        if self.metrics["avg_latency_ms"] > 3000:
            triggered.append(f"延迟告警: {self.metrics['avg_latency_ms']}ms > 3000ms")
        return triggered


# ============================================================
# Step 5: 灰度发布
# ============================================================

class GrayRelease:
    """灰度发布：小步快跑，逐步放量"""

    def __init__(self, ai_ratio=0.1):
        self.ai_ratio = ai_ratio
        self.feedback_log = []

    def should_use_ai(self, user_id):
        return (hash(user_id) % 100) < (self.ai_ratio * 100)

    def record_feedback(self, user_id, question, is_positive):
        self.feedback_log.append({
            "user_id": user_id,
            "question": question[:50],
            "is_positive": is_positive,
            "timestamp": datetime.now().isoformat(),
        })

    def adjust_ratio(self):
        if not self.feedback_log:
            return {"positive_rate": 0, "new_ratio": self.ai_ratio}
        recent = self.feedback_log[-100:]
        positive_rate = sum(1 for f in recent if f["is_positive"]) / len(recent)

        if positive_rate >= 0.85 and self.ai_ratio < 1.0:
            self.ai_ratio = min(self.ai_ratio + 0.1, 1.0)
        elif positive_rate < 0.7 and self.ai_ratio > 0.1:
            self.ai_ratio = max(self.ai_ratio - 0.1, 0.1)

        return {"positive_rate": round(positive_rate, 2), "new_ratio": self.ai_ratio}


# ============================================================
# 演示主流程
# ============================================================

def mock_ai_response(question):
    """模拟AI回答（实际项目中替换为真实LLM调用）"""
    responses = {
        "退货流程怎么走？": "退货流程：7天内申请退货，寄回商品后3个工作日内退款到原支付账户。",
        "订单什么时候发货？": "一般下单后24小时内发货，节假日可能延迟1-2天。",
        "你们公司怎么样？": "我们公司致力于提供优质的产品和服务，欢迎您的咨询。",
        "帮我写一首诗": "抱歉，我是客服助手，暂时无法提供写诗服务，请问有其他问题吗？",
    }
    return responses.get(question, f"关于'{question[:20]}'的问题，建议您联系人工客服获取帮助。")


def main():
    print("=" * 60)
    print("  从Demo到线上的5步生产就绪检查")
    print("=" * 60)

    # --- Step 1: 评估体系 ---
    print("\n=== Step 1: 生产就绪评估 ===")
    evaluator = ProductionReadinessEvaluator()
    evaluator.add_test_case("退货流程怎么走？", ["退货", "退款", "7天"], ["竞品"])
    evaluator.add_test_case("订单什么时候发货？", ["发货", "24小时"], [])
    evaluator.add_test_case("帮我写一首诗", ["抱歉", "客服"], [])

    results = evaluator.run_evaluation(mock_ai_response)
    for r in results:
        print(f"  问题: {r['question']}")
        print(f"  得分: {r['overall']} (关键词:{r['keyword_score']} 安全:{r['safety_score']})")
    print(f"  汇总: {evaluator.summary()}")

    # --- Step 2: Prompt加固 ---
    print("\n=== Step 2: Prompt加固 ===")
    hardener = PromptHardener("你是一个专业的客服助手，只回答与产品相关的问题。")
    hardener.add_guardrail(
        "输入过长", lambda x: len(x) > 500,
        "您的问题过长，请精简后重新提问。"
    )
    hardener.add_guardrail(
        "敏感词检测", lambda x: any(w in x for w in ["密码", "身份证"]),
        "为保护您的隐私，请勿在对话中提供敏感个人信息。"
    )

    test_inputs = ["退货流程怎么走？", "我的密码忘了怎么办", "a" * 600]
    for inp in test_inputs:
        result = hardener.process(inp)
        status = f"拦截({result['reason']})" if result["blocked"] else "通过"
        print(f"  输入: {inp[:30]}... -> {status}")

    # --- Step 3: 工程化防护 ---
    print("\n=== Step 3: 工程化防护 ===")
    guard = ProductionGuard(max_qps=5, daily_token_budget=10000)

    for i in range(8):
        question = f"测试问题{i}"
        if not guard.check_rate_limit():
            print(f"  请求{i}: 被限流")
            continue
        cached = guard.try_cache(question)
        if cached:
            print(f"  请求{i}: 缓存命中")
            continue
        tokens = random.randint(200, 500)
        if not guard.check_budget(tokens):
            print(f"  请求{i}: 预算超限")
            continue
        guard.record_usage(question, f"回答{i}", tokens)
        print(f"  请求{i}: 正常处理 (消耗{tokens} tokens)")

    print(f"  防护状态: {guard.get_status()}")

    # --- Step 4: 可观测性 ---
    print("\n=== Step 4: 可观测性 ===")
    obs = AIObservability()
    for i in range(20):
        latency = random.randint(500, 4000)
        tokens = random.randint(200, 800)
        obs.log_request(f"问题{i}", f"回答{i}", latency, tokens, random.random())
        if random.random() < 0.08:
            obs.report_hallucination()

    print(f"  指标: {obs.metrics}")
    alerts = obs.check_alerts()
    print(f"  告警: {alerts if alerts else '无告警'}")

    # --- Step 5: 灰度发布 ---
    print("\n=== Step 5: 灰度发布 ===")
    gray = GrayRelease(ai_ratio=0.1)
    print(f"  初始灰度比例: {gray.ai_ratio:.0%}")

    for i in range(50):
        user_id = f"user_{i}"
        use_ai = gray.should_use_ai(user_id)
        if use_ai:
            gray.record_feedback(user_id, f"问题{i}", random.random() > 0.15)

    adjustment = gray.adjust_ratio()
    print(f"  反馈好评率: {adjustment['positive_rate']:.0%}")
    print(f"  调整后灰度比例: {adjustment['new_ratio']:.0%}")

    print("\n" + "=" * 60)
    print("  5步检查完成！系统已具备生产就绪条件")
    print("=" * 60)


if __name__ == "__main__":
    main()
