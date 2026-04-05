"""
智能客服系统演示：RAG + 工作流 + 人工兜底
对应文章：77-智能客服从0到1-RAG加工作流加人工兜底全实现
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class KnowledgeItem:
    doc_id: str
    question: str
    answer: str
    category: str
    keywords: list[str] = field(default_factory=list)


class IntentClassifier:
    """基于关键词的意图识别"""
    INTENT_RULES = {
        "refund": ["退货", "退款", "退回", "不想要"],
        "shipping": ["发货", "物流", "快递", "配送", "到货"],
        "product": ["产品", "功能", "怎么用", "使用", "说明"],
        "complaint": ["投诉", "差评", "垃圾", "骗子", "举报"],
    }

    def classify(self, text: str) -> tuple[str, float]:
        best_intent, best_score = "general", 0.3
        for intent, keywords in self.INTENT_RULES.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                score = min(matches / len(keywords) + 0.5, 1.0)
                if score > best_score:
                    best_intent, best_score = intent, score
        return best_intent, round(best_score, 2)


class SimpleRAG:
    """简化版RAG检索"""
    def __init__(self):
        self.knowledge: list[KnowledgeItem] = []

    def add_knowledge(self, item: KnowledgeItem):
        self.knowledge.append(item)

    def search(self, query: str, category: str | None = None,
               top_k: int = 3) -> list[dict]:
        results = []
        for item in self.knowledge:
            if category and item.category != category and category != "general":
                continue
            score = self._similarity(query, item)
            results.append({"item": item, "score": round(score, 3)})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _similarity(self, query: str, item: KnowledgeItem) -> float:
        q_chars = set(query)
        kw_chars = set(item.question) | set("".join(item.keywords))
        if not kw_chars:
            return 0.0
        return len(q_chars & kw_chars) / len(q_chars | kw_chars)


class HumanEscalation:
    """人工兜底管理"""
    def __init__(self, confidence_threshold: float = 0.4,
                 sensitive_intents: list[str] | None = None,
                 max_turns: int = 5):
        self.confidence_threshold = confidence_threshold
        self.sensitive_intents = sensitive_intents or ["complaint"]
        self.max_turns = max_turns

    def should_escalate(self, confidence: float, intent: str,
                        turn_count: int) -> tuple[bool, str]:
        if intent in self.sensitive_intents:
            return True, "sensitive_topic"
        if confidence < self.confidence_threshold:
            return True, "low_confidence"
        if turn_count >= self.max_turns:
            return True, "max_turns_exceeded"
        return False, ""


class CustomerServiceBot:
    """智能客服主控"""
    def __init__(self):
        self.classifier = IntentClassifier()
        self.rag = SimpleRAG()
        self.escalation = HumanEscalation()
        self.conversations: dict[str, list[dict]] = {}

    def load_knowledge(self, items: list[KnowledgeItem]):
        for item in items:
            self.rag.add_knowledge(item)

    def handle_message(self, user_id: str, message: str) -> dict:
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        history = self.conversations[user_id]
        turn = len(history) + 1

        # 1. 意图识别
        intent, intent_conf = self.classifier.classify(message)

        # 2. 检查是否需要转人工
        escalate, reason = self.escalation.should_escalate(
            intent_conf, intent, turn)
        if escalate:
            history.append({"role": "user", "content": message})
            history.append({"role": "system", "content": f"转人工: {reason}"})
            return {
                "type": "escalation", "reason": reason,
                "intent": intent, "turn": turn,
                "summary": self._summarize(history),
            }

        # 3. RAG检索
        results = self.rag.search(message, category=intent)
        if not results or results[0]["score"] < 0.1:
            history.append({"role": "user", "content": message})
            reply = "抱歉，我暂时无法回答这个问题，正在为您转接人工客服。"
            history.append({"role": "assistant", "content": reply})
            return {"type": "escalation", "reason": "no_match",
                    "intent": intent, "turn": turn, "reply": reply}

        # 4. 生成回答
        best = results[0]
        reply = best["item"].answer
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})

        return {
            "type": "answer", "reply": reply,
            "intent": intent, "confidence": intent_conf,
            "rag_score": best["score"], "turn": turn,
            "source": best["item"].doc_id,
        }

    def _summarize(self, history: list[dict]) -> str:
        user_msgs = [h["content"] for h in history if h["role"] == "user"]
        return f"用户共{len(user_msgs)}轮对话，最后问题：{user_msgs[-1] if user_msgs else '无'}"


def build_knowledge_base() -> list[KnowledgeItem]:
    return [
        KnowledgeItem("k1", "退货流程怎么走",
                       "退货流程：1.在订单页点击申请退货 2.选择退货原因 "
                       "3.等待审核(1个工作日) 4.寄回商品 5.收到退款(3-5个工作日)",
                       "refund", ["退货", "退款", "流程"]),
        KnowledgeItem("k2", "发货后多久能到",
                       "标准配送3-5个工作日，加急配送1-2个工作日。"
                       "您可以在订单详情页查看物流信息。",
                       "shipping", ["发货", "配送", "物流", "到货"]),
        KnowledgeItem("k3", "产品怎么使用",
                       "请参考产品包装内的快速入门指南。也可以在App内搜索"
                       "'使用教程'查看视频教程。",
                       "product", ["使用", "教程", "功能"]),
        KnowledgeItem("k4", "退款多久到账",
                       "退款审核通过后，原路退回：支付宝1-3天，"
                       "微信3-5天，银行卡5-10个工作日。",
                       "refund", ["退款", "到账", "多久"]),
        KnowledgeItem("k5", "如何修改收货地址",
                       "未发货订单可在订单详情页直接修改地址。"
                       "已发货订单请联系快递公司转寄。",
                       "shipping", ["地址", "修改", "收货"]),
    ]


def main():
    bot = CustomerServiceBot()
    knowledge = build_knowledge_base()
    bot.load_knowledge(knowledge)

    print("=" * 60)
    print("智能客服系统演示")
    print("=" * 60)

    # 加载知识库
    print(f"\n--- 1. 知识库加载 ---")
    print(f"  已加载 {len(knowledge)} 条知识")
    for k in knowledge:
        print(f"    [{k.doc_id}] {k.question} ({k.category})")

    # 模拟对话
    test_cases = [
        ("user1", "退货流程怎么走？"),
        ("user1", "退款多久能到账？"),
        ("user2", "快递什么时候到？"),
        ("user3", "你们这个产品是垃圾！我要投诉！"),
        ("user4", "今天天气怎么样？"),
    ]

    print(f"\n--- 2. 对话模拟 ---")
    for user_id, message in test_cases:
        print(f"\n  [{user_id}] 用户: {message}")
        result = bot.handle_message(user_id, message)

        if result["type"] == "answer":
            print(f"  🤖 AI: {result['reply']}")
            print(f"     意图={result['intent']} 置信度={result['confidence']} "
                  f"RAG={result['rag_score']} 来源={result['source']}")
        else:
            print(f"  🔴 转人工: {result['reason']}")
            if "summary" in result:
                print(f"     摘要: {result['summary']}")
            if "reply" in result:
                print(f"  🤖 AI: {result['reply']}")

    # 多轮对话演示
    print(f"\n--- 3. 多轮对话 ---")
    multi_turn = [
        ("user5", "我想退货"),
        ("user5", "退款多久到"),
        ("user5", "太慢了"),
        ("user5", "还是太慢"),
        ("user5", "我不满意"),
        ("user5", "再说一遍"),
    ]
    for user_id, msg in multi_turn:
        result = bot.handle_message(user_id, msg)
        turn = result.get("turn", "?")
        if result["type"] == "answer":
            print(f"  [轮次{turn}] {msg} -> AI回答 (置信度{result['confidence']})")
        else:
            print(f"  [轮次{turn}] {msg} -> 🔴转人工 ({result['reason']})")
            break

    # 统计
    print(f"\n--- 4. 会话统计 ---")
    for uid, hist in bot.conversations.items():
        user_turns = sum(1 for h in hist if h["role"] == "user")
        escalated = any(h["role"] == "system" for h in hist)
        status = "已转人工" if escalated else "AI处理中"
        print(f"  {uid}: {user_turns}轮对话, {status}")


if __name__ == "__main__":
    main()
