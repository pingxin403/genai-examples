"""
AI应用示例：概率性问答服务（模拟版）

演示概率性系统的典型特征：
- 同输入可能不同输出
- 错误是隐性的（"微笑失败"）
- 需要置信度判断 + 降级策略
- 测试用评估集 + 通过率门槛

对应文章：《写CRUD和写AI应用，到底有什么不一样？》

注意：本示例使用模拟LLM响应，无需真实API Key即可运行。
"""

import random
import json
import time
from dataclasses import dataclass
from typing import List, Optional


# ========== 质量门控定义 ==========

QUALITY_GATE = {
    "faithfulness_min": 0.8,
    "helpfulness_min": 0.7,
    "safety_must_pass": True,
    "max_tokens_budget": 2000,
}

CONFIDENCE_THRESHOLDS = {
    "high": 0.85,   # 直接返回
    "medium": 0.65,  # 附带引用返回
    "low": 0.0,      # 降级/转人工
}


# ========== 数据模型 ==========

@dataclass
class AIResponse:
    answer: str
    confidence: float
    tokens_used: int
    citations: List[str]
    action: str = ""  # direct / cited / fallback


@dataclass
class EvalCase:
    question: str
    expected_traits: List[str]


# ========== 模拟LLM服务 ==========

class MockLLMService:
    """模拟LLM服务，展示概率性输出特征"""

    KNOWLEDGE_BASE = {
        "退货流程": [
            "退货流程：1.提交退货申请 2.等待审核(1-2工作日) 3.寄回商品 4.确认收货后退款",
            "退货步骤：先在订单页点击退货，填写原因，审核通过后按地址寄回，我们收到后3天内退款",
            "您好！退货很简单：申请→审核→寄回→退款。整个流程大约5-7个工作日。",
        ],
        "配送时间": [
            "标准配送3-5个工作日，加急配送1-2个工作日，偏远地区可能延长1-2天",
            "一般3到5天送达，急件可选加急配送，次日或隔日到",
        ],
    }

    def generate(self, question: str) -> AIResponse:
        """模拟LLM生成 —— 同一问题可能返回不同答案"""
        time.sleep(random.uniform(0.1, 0.5))  # 模拟推理延迟

        # 模拟知识检索
        matched_key = None
        for key in self.KNOWLEDGE_BASE:
            if key in question:
                matched_key = key
                break

        if matched_key:
            answers = self.KNOWLEDGE_BASE[matched_key]
            answer = random.choice(answers)  # 概率性：随机选择一个回答
            confidence = random.uniform(0.6, 0.95)
            tokens = random.randint(150, 500)
            citations = [f"知识库/{matched_key}/doc_{random.randint(1,5)}"]
        else:
            answer = "抱歉，我暂时无法回答这个问题，建议联系人工客服获取帮助。"
            confidence = random.uniform(0.1, 0.4)
            tokens = random.randint(50, 150)
            citations = []

        return AIResponse(
            answer=answer,
            confidence=confidence,
            tokens_used=tokens,
            citations=citations,
        )


# ========== AI工程化流水线 ==========

class AIServicePipeline:
    """工程化的AI服务流水线"""

    def __init__(self):
        self.llm = MockLLMService()
        self.total_tokens = 0
        self.request_count = 0

    def answer(self, question: str) -> AIResponse:
        """完整的AI问答流水线"""
        self.request_count += 1

        # Step 1: 预算检查
        if self.total_tokens > QUALITY_GATE["max_tokens_budget"] * 10:
            return AIResponse(
                answer="今日对话额度已用完，请明天再来",
                confidence=1.0,
                tokens_used=0,
                citations=[],
                action="budget_exceeded",
            )

        # Step 2: 调用LLM（带超时模拟）
        try:
            result = self.llm.generate(question)
        except Exception:
            return AIResponse(
                answer="系统繁忙，请稍后再试",
                confidence=0.0,
                tokens_used=0,
                citations=[],
                action="error_fallback",
            )

        # Step 3: 置信度路由
        result.action = self._route_by_confidence(result)

        # Step 4: 记录Token消耗
        self.total_tokens += result.tokens_used

        return result

    def _route_by_confidence(self, result: AIResponse) -> str:
        """根据置信度决定响应策略"""
        if result.confidence >= CONFIDENCE_THRESHOLDS["high"]:
            return "direct"       # 高置信：直接返回
        elif result.confidence >= CONFIDENCE_THRESHOLDS["medium"]:
            return "cited"        # 中置信：附带引用
        else:
            result.answer = "该问题需要人工客服协助，正在为您转接..."
            return "fallback"     # 低置信：转人工


# ========== 评估集测试 ==========

def evaluate_with_eval_set(service: AIServicePipeline) -> float:
    """用评估集测试AI服务 —— 不是断言精确值，而是断言特征+通过率"""
    eval_set = [
        EvalCase("退货流程怎么走？", ["退货", "申请", "退款"]),
        EvalCase("配送要多久？", ["配送", "工作日"]),
        EvalCase("退货流程", ["退货", "寄回"]),
    ]

    passed = 0
    for case in eval_set:
        result = service.answer(case.question)
        # 特征断言：检查回答是否包含期望的关键特征
        traits_matched = sum(
            1 for trait in case.expected_traits if trait in result.answer
        )
        if traits_matched >= len(case.expected_traits) * 0.5:
            passed += 1

    return passed / len(eval_set)


# ========== 运行演示 ==========

def main():
    print("=== AI应用示例：概率性系统 ===\n")

    service = AIServicePipeline()

    # 演示1：同一问题多次调用，结果可能不同
    print("--- 演示：概率性输出 ---")
    question = "退货流程怎么走？"
    for i in range(3):
        result = service.answer(question)
        print(f"  第{i+1}次调用:")
        print(f"    问题: {question}")
        print(f"    回答: {result.answer}")
        print(f"    置信度: {result.confidence:.2f}")
        print(f"    策略: {result.action}")
        print(f"    Token: {result.tokens_used}")
        print()

    print("→ 同一个问题，三次调用可能得到不同的回答和置信度\n")

    # 演示2：未知问题的降级处理
    print("--- 演示：降级策略 ---")
    unknown_q = "你们CEO是谁？"
    result = service.answer(unknown_q)
    print(f"  问题: {unknown_q}")
    print(f"  回答: {result.answer}")
    print(f"  策略: {result.action}")
    print(f"  → 低置信度问题自动降级到人工\n")

    # 演示3：评估集测试
    print("--- 演示：评估集测试（替代单元测试） ---")
    pass_rate = evaluate_with_eval_set(service)
    print(f"  评估集通过率: {pass_rate:.0%}")
    print(f"  门槛: 85%")
    print(f"  结果: {'✅ 通过' if pass_rate >= 0.85 else '❌ 未通过，需优化'}")
    print()

    # 演示4：成本统计
    print("--- 演示：Token成本统计 ---")
    print(f"  总请求数: {service.request_count}")
    print(f"  总Token消耗: {service.total_tokens}")
    print(f"  平均Token/请求: {service.total_tokens / max(service.request_count, 1):.0f}")
    print()

    print("=== AI应用核心特征 ===")
    print("1. 概率性：同输入 → 可能不同输出")
    print("2. 隐性错误：回答看似正常但可能不符合业务要求")
    print("3. 评估测试：用评估集+通过率，而非精确断言")
    print("4. 成本波动：Token消耗与输入内容相关，非线性")
    print("5. 降级必备：低置信度必须有兜底策略")


if __name__ == "__main__":
    main()
