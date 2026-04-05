"""
Prompt工程进化的四个阶段 — 完整演示
配套文章：《从零样本到思维链：Prompt工程进化的四个阶段》

演示内容：
1. 零样本（Zero-Shot）：直接提问
2. 少样本（Few-Shot）：示例引导
3. 思维链（Chain-of-Thought）：逐步推理
4. 自洽性（Self-Consistency）：多次采样投票
"""

import random
from collections import Counter


# ============================================================
# 阶段1：零样本（Zero-Shot）
# ============================================================

class ZeroShotPrompt:
    """零样本Prompt：直接描述任务，不提供示例"""

    def build(self, task_description: str, user_input: str) -> str:
        return f"""{task_description}

输入：{user_input}
输出："""

    def classify_sentiment(self, text: str) -> str:
        return self.build(
            "请判断以下文本的情感倾向，只回答：正面、负面、中性。",
            text,
        )

    def extract_keywords(self, text: str) -> str:
        return self.build(
            "请从以下文本中提取3-5个关键词，用逗号分隔。",
            text,
        )


# ============================================================
# 阶段2：少样本（Few-Shot）
# ============================================================

class FewShotPrompt:
    """少样本Prompt：通过示例引导模型输出格式和风格"""

    def __init__(self):
        self.examples: list[dict] = []

    def add_example(self, input_text: str, output_text: str):
        self.examples.append({"input": input_text, "output": output_text})

    def build(self, task_description: str, user_input: str) -> str:
        prompt = task_description + "\n\n"
        for i, ex in enumerate(self.examples, 1):
            prompt += f"示例{i}：\n输入：{ex['input']}\n输出：{ex['output']}\n\n"
        prompt += f"现在请处理：\n输入：{user_input}\n输出："
        return prompt

    def clear_examples(self):
        self.examples = []


# ============================================================
# 阶段3：思维链（Chain-of-Thought）
# ============================================================

class ChainOfThoughtPrompt:
    """思维链Prompt：引导模型逐步推理，展示思考过程"""

    def build_with_reasoning(self, task: str, user_input: str) -> str:
        return f"""{task}

请按以下步骤分析：
1. 首先，识别关键信息
2. 然后，逐条分析每个要素
3. 接着，综合判断风险等级
4. 最后，给出结论和建议

输入：{user_input}

让我们一步步来分析："""

    def analyze_contract_risk(self, contract_text: str) -> str:
        return self.build_with_reasoning(
            "你是一位资深法务专家。请分析以下合同条款的潜在风险。",
            contract_text,
        )

    def solve_math_problem(self, problem: str) -> str:
        return self.build_with_reasoning(
            "你是一位数学老师。请解答以下数学问题。",
            problem,
        )


# ============================================================
# 阶段4：自洽性（Self-Consistency）
# ============================================================

class SelfConsistencyPrompt:
    """自洽性Prompt：多次采样 + 投票，提高推理可靠性"""

    def __init__(self, num_samples: int = 5, temperature: float = 0.7):
        self.num_samples = num_samples
        self.temperature = temperature
        self.cot = ChainOfThoughtPrompt()

    def sample_and_vote(self, task: str, user_input: str, llm_call_fn) -> dict:
        """多次采样并投票"""
        results = []
        for _ in range(self.num_samples):
            prompt = self.cot.build_with_reasoning(task, user_input)
            response = llm_call_fn(prompt, temperature=self.temperature)
            conclusion = self.extract_conclusion(response)
            results.append(conclusion)

        # 投票：取出现次数最多的结论
        vote_counts = Counter(results)
        best_answer = vote_counts.most_common(1)[0]

        return {
            "answer": best_answer[0],
            "confidence": round(best_answer[1] / self.num_samples, 2),
            "all_results": results,
            "vote_distribution": dict(vote_counts),
        }

    @staticmethod
    def extract_conclusion(response: str) -> str:
        """从推理过程中提取最终结论"""
        lines = response.strip().split("\n")
        for line in reversed(lines):
            if any(kw in line for kw in ["结论", "判断", "结果", "答案"]):
                return line.strip()
        return lines[-1].strip() if lines else "无法判断"


# ============================================================
# 模拟LLM调用（用于演示，不依赖真实API）
# ============================================================

def mock_llm_call(prompt: str, temperature: float = 0.0) -> str:
    """模拟LLM调用，根据Prompt类型返回不同风格的回答"""
    if "情感倾向" in prompt:
        if temperature > 0.5:
            return random.choice(["正面", "正面", "正面", "中性"])
        return "正面"

    if "关键词" in prompt:
        return "AI工程, Prompt设计, 大模型, 思维链"

    if "一步步" in prompt or "步骤" in prompt:
        risk_levels = ["高风险", "高风险", "高风险", "中风险", "高风险"]
        chosen = random.choice(risk_levels) if temperature > 0.5 else "高风险"
        return f"""步骤1：识别关键信息 — 合同中包含"不可抗力"和"单方解除"条款
步骤2：逐条分析 — "不可抗力"定义模糊，可能被滥用；"单方解除"缺少对等条件
步骤3：综合判断 — 两个条款组合存在较大风险
步骤4：结论 — 风险等级：{chosen}，建议增加不可抗力的具体定义和对等解除条件"""

    return "这是一个模拟回答。"


# ============================================================
# 演示主流程
# ============================================================

def demo_zero_shot():
    """演示零样本"""
    print("=" * 60)
    print("阶段1：零样本（Zero-Shot）")
    print("=" * 60)

    zs = ZeroShotPrompt()

    # 情感分类
    prompt = zs.classify_sentiment("这个产品太好用了，强烈推荐！")
    response = mock_llm_call(prompt)
    print(f"\n[情感分类]")
    print(f"Prompt:\n{prompt}")
    print(f"回答: {response}")

    # 关键词提取
    prompt = zs.extract_keywords("Prompt工程是AI应用开发中的核心技能，涵盖零样本、少样本、思维链等技术。")
    response = mock_llm_call(prompt)
    print(f"\n[关键词提取]")
    print(f"回答: {response}")
    print()


def demo_few_shot():
    """演示少样本"""
    print("=" * 60)
    print("阶段2：少样本（Few-Shot）")
    print("=" * 60)

    fs = FewShotPrompt()
    fs.add_example(
        "姓名：张三，年龄：28，职位：工程师",
        '{"name": "张三", "age": 28, "role": "工程师"}',
    )
    fs.add_example(
        "李四 35岁 产品经理",
        '{"name": "李四", "age": 35, "role": "产品经理"}',
    )
    fs.add_example(
        "王五/42/CTO",
        '{"name": "王五", "age": 42, "role": "CTO"}',
    )

    prompt = fs.build(
        "请将以下人员信息转换为JSON格式。",
        "赵六 29岁 做设计的",
    )
    print(f"\n[数据提取]")
    print(f"Prompt:\n{prompt}")
    print(f"预期输出: " + '{"name": "赵六", "age": 29, "role": "设计师"}')
    print()


def demo_chain_of_thought():
    """演示思维链"""
    print("=" * 60)
    print("阶段3：思维链（Chain-of-Thought）")
    print("=" * 60)

    cot = ChainOfThoughtPrompt()
    contract = "甲方可在不可抗力情况下单方解除合同，且无需承担违约责任。"
    prompt = cot.analyze_contract_risk(contract)
    response = mock_llm_call(prompt)
    print(f"\n[合同风险分析]")
    print(f"Prompt:\n{prompt}")
    print(f"\n回答:\n{response}")
    print()


def demo_self_consistency():
    """演示自洽性"""
    print("=" * 60)
    print("阶段4：自洽性（Self-Consistency）")
    print("=" * 60)

    sc = SelfConsistencyPrompt(num_samples=5, temperature=0.7)
    result = sc.sample_and_vote(
        "你是一位资深法务专家。请分析以下合同条款的潜在风险。",
        "甲方可在不可抗力情况下单方解除合同，且无需承担违约责任。",
        mock_llm_call,
    )
    print(f"\n[自洽性投票结果]")
    print(f"最终答案: {result['answer']}")
    print(f"置信度: {result['confidence']}")
    print(f"投票分布: {result['vote_distribution']}")
    print(f"所有采样结果: {result['all_results']}")
    print()


def demo_comparison():
    """效果对比总结"""
    print("=" * 60)
    print("效果对比总结")
    print("=" * 60)

    comparison = [
        ("零样本 Zero-Shot", "62%", "1.2s", "180", "低", "简单分类、翻译"),
        ("少样本 Few-Shot", "78%", "1.8s", "520", "中", "格式化输出、数据提取"),
        ("思维链 CoT", "87%", "2.5s", "680", "中高", "复杂推理、逻辑分析"),
        ("自洽性 SC", "93%", "12s", "3400", "高", "高可靠性推理任务"),
    ]

    header = f"{'阶段':<20} {'准确率':<8} {'延迟':<8} {'Token':<8} {'成本':<6} {'适用场景'}"
    print(f"\n{header}")
    print("-" * 80)
    for row in comparison:
        print(f"{row[0]:<20} {row[1]:<8} {row[2]:<8} {row[3]:<8} {row[4]:<6} {row[5]}")
    print()


if __name__ == "__main__":
    print("\n🧩 Prompt工程进化的四个阶段 — 完整演示\n")

    demo_zero_shot()
    demo_few_shot()
    demo_chain_of_thought()
    demo_self_consistency()
    demo_comparison()

    print("✅ 演示完成！")
    print("💡 提示：根据任务复杂度选择合适的阶段，不是越高级越好。")
