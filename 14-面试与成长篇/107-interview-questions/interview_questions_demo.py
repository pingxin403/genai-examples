"""AI工程化高频面试题演示：题库、评分、知识覆盖"""


class InterviewQuestionBank:
    def __init__(self):
        self.questions: list[dict] = []

    def add(self, cat: str, q: str, key_points: list[str], diff: int):
        self.questions.append({"category": cat, "question": q,
                              "key_points": key_points, "difficulty": diff})

    def by_category(self, cat: str) -> list[dict]:
        return [q for q in self.questions if q["category"] == cat]

    def evaluate(self, idx: int, answer_points: list[str]) -> dict:
        q = self.questions[idx]
        covered = [kp for kp in q["key_points"]
                   if any(kp in ap for ap in answer_points)]
        return {"score": f"{len(covered)}/{len(q['key_points'])}",
                "covered": covered,
                "missed": [kp for kp in q["key_points"] if kp not in covered]}


def main():
    print("=" * 60)
    print("AI工程化高频面试题演示")
    print("=" * 60)

    bank = InterviewQuestionBank()
    bank.add("RAG", "RAG召回率下降怎么排查？",
             ["分块策略", "Embedding质量", "检索配置", "上下文拼接"], 4)
    bank.add("RAG", "分块策略怎么选？",
             ["语义分块", "固定分块", "文档类型", "重叠窗口"], 3)
    bank.add("Agent", "Agent死循环怎么防？",
             ["最大迭代", "重复检测", "成本封顶", "人工介入"], 4)
    bank.add("Agent", "工具调用的安全边界？",
             ["权限分级", "审批机制", "审计日志", "最小权限"], 4)
    bank.add("Prompt", "Prompt版本管理怎么做？",
             ["Git管理", "回归测试", "灰度发布", "效果跟踪"], 3)
    bank.add("评估", "如何评估RAG系统效果？",
             ["召回率", "忠实度", "用户满意度", "在线指标"], 4)

    print("\n--- 题库概览 ---")
    for cat in ["RAG", "Agent", "Prompt", "评估"]:
        qs = bank.by_category(cat)
        print(f"  {cat}: {len(qs)}题")
        for q in qs:
            print(f"    ⭐{'⭐' * q['difficulty']} {q['question']}")

    print("\n--- 模拟评分 ---")
    answer = ["分块策略", "Embedding质量", "检索配置"]
    result = bank.evaluate(0, answer)
    print(f"  问题: {bank.questions[0]['question']}")
    print(f"  得分: {result['score']}")
    print(f"  覆盖: {result['covered']}")
    print(f"  遗漏: {result['missed']}")

    print(f"\n{'=' * 60}")
    print("核心: 理论+实战案例+系统设计 = 面试通关")
    print("=" * 60)


if __name__ == "__main__":
    main()
