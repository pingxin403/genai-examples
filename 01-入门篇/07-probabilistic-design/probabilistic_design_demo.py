"""
概率性系统的三层防御演示
对应文章：⚖️《概率性系统的设计哲学：接受不完美，但可控》

演示内容：
1. 置信度评估器：综合多个信号判断AI回答的可信程度
2. 多级回退策略：缓存→规则引擎→安全话术的梯度降级
3. 人工兜底调度：工作时间转人工，非工作时间创建工单
4. 完整防御流程：三层联动处理不同置信度的请求
"""

from datetime import datetime


# ============================================================
# 第一层：置信度评估器
# ============================================================

class ConfidenceEvaluator:
    """评估AI回答的置信度，决定是否可以直接返回"""

    def __init__(self, high_threshold=0.85, low_threshold=0.5):
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold

    def evaluate(self, question, answer, retrieval_scores=None):
        score = 0.0
        signals = []

        # 信号1：检索相关性（RAG场景）
        if retrieval_scores:
            top_score = max(retrieval_scores)
            score += top_score * 0.4
            signals.append(f"检索相关性: {top_score:.2f}")

        # 信号2：回答长度合理性
        length_ratio = min(len(answer) / max(len(question) * 3, 50), 1.0)
        score += length_ratio * 0.2
        signals.append(f"长度合理性: {length_ratio:.2f}")

        # 信号3：是否包含不确定表述
        uncertain_phrases = ["我不确定", "可能", "也许", "不太清楚"]
        has_uncertainty = any(p in answer for p in uncertain_phrases)
        certainty_score = 0.0 if has_uncertainty else 0.4
        score += certainty_score
        signals.append(f"确定性: {certainty_score:.2f}")

        return {
            "score": round(score, 3),
            "level": self._classify(score),
            "signals": signals,
        }

    def _classify(self, score):
        if score >= self.high_threshold:
            return "high"
        elif score >= self.low_threshold:
            return "medium"
        return "low"


# ============================================================
# 第二层：多级回退策略
# ============================================================

class FallbackChain:
    """多级回退：AI不确定时，依次尝试缓存、规则引擎、安全话术"""

    def __init__(self):
        self.cache = {}
        self.rules = {}
        self.safe_response = (
            "抱歉，这个问题我暂时无法准确回答，建议您联系人工客服获取帮助。"
        )

    def add_cache(self, question_pattern, answer):
        self.cache[question_pattern] = answer

    def add_rule(self, keyword, answer):
        self.rules[keyword] = answer

    def fallback(self, question):
        # 第一级回退：精确缓存匹配
        if question in self.cache:
            return {"answer": self.cache[question], "source": "cache"}

        # 第二级回退：关键词规则匹配
        for keyword, answer in self.rules.items():
            if keyword in question:
                return {"answer": answer, "source": "rule_engine"}

        # 第三级回退：安全话术
        return {"answer": self.safe_response, "source": "safe_fallback"}


# ============================================================
# 第三层：人工兜底调度器
# ============================================================

class HumanEscalation:
    """人工兜底：机器搞不定的交给人"""

    def __init__(self):
        self.ticket_queue = []
        self.work_hours = (9, 18)  # 工作时间9:00-18:00

    def escalate(self, question, ai_answer, confidence_score):
        current_hour = datetime.now().hour
        is_work_time = self.work_hours[0] <= current_hour < self.work_hours[1]

        ticket = {
            "question": question,
            "ai_answer": ai_answer,
            "confidence": confidence_score,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
        self.ticket_queue.append(ticket)

        if is_work_time:
            return {
                "action": "transfer_human",
                "message": "正在为您转接人工客服，请稍候...",
                "ticket_id": len(self.ticket_queue),
            }
        else:
            return {
                "action": "create_ticket",
                "message": "当前为非工作时间，已为您创建工单，客服将在工作时间内回复您。",
                "ticket_id": len(self.ticket_queue),
            }


# ============================================================
# 完整防御流程演示
# ============================================================

def demo_probabilistic_defense():
    """演示概率性系统的三层防御"""

    print("=" * 60)
    print("⚖️  概率性系统三层防御演示")
    print("=" * 60)

    # 初始化三层防御
    evaluator = ConfidenceEvaluator(high_threshold=0.85, low_threshold=0.5)
    fallback = FallbackChain()
    escalation = HumanEscalation()

    # 预置缓存和规则
    fallback.add_cache(
        "退货流程怎么走？",
        "退货流程：7天内申请→寄回商品→3个工作日退款。",
    )
    fallback.add_rule("投诉", "投诉请拨打400-XXX-XXXX，工作时间9:00-18:00。")
    fallback.add_rule("营业时间", "营业时间：周一至周五 9:00-18:00。")

    # 模拟不同置信度的请求
    test_cases = [
        {
            "question": "退款多久到账？",
            "ai_answer": "一般3-5个工作日到账，具体以银行处理时间为准。",
            "retrieval_scores": [0.92, 0.85, 0.71],
        },
        {
            "question": "你们的产品质量怎么样？",
            "ai_answer": "我们的产品可能还不错吧，我不确定具体的质量报告。",
            "retrieval_scores": [0.45, 0.32, 0.28],
        },
        {
            "question": "能帮我写一首诗吗？",
            "ai_answer": "好的，让我试试...",
            "retrieval_scores": [0.12, 0.08, 0.05],
        },
        {
            "question": "退货流程怎么走？",
            "ai_answer": "退货也许需要联系客服吧，我不太清楚具体流程。",
            "retrieval_scores": [0.60, 0.55, 0.40],
        },
        {
            "question": "我要投诉你们的服务！",
            "ai_answer": "我不确定投诉流程，可能需要打电话。",
            "retrieval_scores": [0.50, 0.35, 0.20],
        },
    ]

    stats = {"high": 0, "medium": 0, "low": 0}

    for case in test_cases:
        print(f"\n{'─' * 60}")
        print(f"📩 用户问题: {case['question']}")

        # 第一层：置信度评估
        conf = evaluator.evaluate(
            case["question"], case["ai_answer"], case["retrieval_scores"]
        )
        print(f"📊 置信度: {conf['score']} ({conf['level']})")
        print(f"   信号: {' | '.join(conf['signals'])}")

        stats[conf["level"]] += 1

        if conf["level"] == "high":
            print(f"✅ 直接返回AI结果: {case['ai_answer']}")
        elif conf["level"] == "medium":
            fb = fallback.fallback(case["question"])
            print(f"⚠️  触发回退策略 [{fb['source']}]: {fb['answer']}")
        else:
            result = escalation.escalate(
                case["question"], case["ai_answer"], conf["score"]
            )
            print(f"🚨 触发人工兜底 [{result['action']}]: {result['message']}")

    # 统计汇总
    total = len(test_cases)
    print(f"\n{'=' * 60}")
    print("📈 防御层级统计")
    print(f"   AI直接回答: {stats['high']}/{total} ({stats['high']/total:.0%})")
    print(f"   回退策略:   {stats['medium']}/{total} ({stats['medium']/total:.0%})")
    print(f"   人工兜底:   {stats['low']}/{total} ({stats['low']/total:.0%})")
    print(f"   待处理工单: {len(escalation.ticket_queue)}")
    print("=" * 60)


if __name__ == "__main__":
    demo_probabilistic_defense()
