"""
AI应用迭代Pipeline演示
对应文章：🔄《AI应用怎么迭代？和传统CI/CD完全不一样》

演示内容：
1. Prompt版本管理
2. 评估集驱动验证
3. 用户反馈回流
4. 完整迭代流程串联
"""

import json
from datetime import datetime


# ============================================================
# 模块1：Prompt版本管理
# ============================================================

class PromptVersionManager:
    """Prompt版本管理：像管理代码一样管理Prompt"""

    def __init__(self):
        self.versions = {}
        self.active_version = None

    def register(self, version_id, template, description=""):
        self.versions[version_id] = {
            "template": template,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "metrics": {"requests": 0, "thumbs_up": 0, "thumbs_down": 0},
        }
        if self.active_version is None:
            self.active_version = version_id

    def get_prompt(self, version_id=None):
        vid = version_id or self.active_version
        return self.versions[vid]["template"]

    def switch_active(self, version_id):
        if version_id in self.versions:
            self.active_version = version_id

    def record_feedback(self, version_id, is_positive):
        v = self.versions[version_id]
        v["metrics"]["requests"] += 1
        if is_positive:
            v["metrics"]["thumbs_up"] += 1
        else:
            v["metrics"]["thumbs_down"] += 1

    def get_adoption_rate(self, version_id):
        m = self.versions[version_id]["metrics"]
        total = m["thumbs_up"] + m["thumbs_down"]
        return m["thumbs_up"] / total if total > 0 else 0.0


# ============================================================
# 模块2：评估集驱动验证
# ============================================================

class EvaluationRunner:
    """评估集验证：每次Prompt变更前必须跑评估"""

    def __init__(self):
        self.eval_set = []

    def add_case(self, question, expected_keywords, blocked_keywords=None):
        self.eval_set.append({
            "question": question,
            "expected_keywords": expected_keywords,
            "blocked_keywords": blocked_keywords or [],
        })

    def run(self, generate_fn):
        results = []
        for case in self.eval_set:
            answer = generate_fn(case["question"])
            # 检查期望关键词是否出现
            hits = sum(1 for kw in case["expected_keywords"] if kw in answer)
            keyword_score = hits / len(case["expected_keywords"])
            # 检查禁止关键词是否出现
            blocked_hits = sum(
                1 for kw in case["blocked_keywords"] if kw in answer
            )
            is_safe = blocked_hits == 0

            results.append({
                "question": case["question"],
                "keyword_score": keyword_score,
                "is_safe": is_safe,
                "pass": keyword_score >= 0.6 and is_safe,
            })

        pass_count = sum(1 for r in results if r["pass"])
        return {
            "total": len(results),
            "passed": pass_count,
            "pass_rate": pass_count / len(results) if results else 0,
            "details": results,
        }


# ============================================================
# 模块3：用户反馈回流
# ============================================================

class FeedbackCollector:
    """用户反馈采集与数据回流"""

    def __init__(self):
        self.feedback_log = []

    def collect(self, question, answer, prompt_version, is_positive, comment=""):
        self.feedback_log.append({
            "question": question,
            "answer": answer,
            "prompt_version": prompt_version,
            "is_positive": is_positive,
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
        })

    def get_negative_cases(self):
        """提取负面反馈，用于扩充评估集"""
        return [f for f in self.feedback_log if not f["is_positive"]]

    def generate_eval_candidates(self):
        """从负面反馈中生成评估集候选"""
        negatives = self.get_negative_cases()
        candidates = []
        for item in negatives:
            candidates.append({
                "question": item["question"],
                "bad_answer": item["answer"],
                "user_comment": item["comment"],
            })
        return candidates

    def summary(self):
        total = len(self.feedback_log)
        positive = sum(1 for f in self.feedback_log if f["is_positive"])
        return {
            "total_feedback": total,
            "positive": positive,
            "negative": total - positive,
            "satisfaction_rate": positive / total if total > 0 else 0,
        }


# ============================================================
# 完整迭代流程演示
# ============================================================

def demo_iteration_pipeline():
    """演示完整的AI迭代Pipeline"""

    print("=" * 60)
    print("🔄 AI应用迭代Pipeline演示")
    print("=" * 60)

    # 1. 初始化Prompt版本管理
    pm = PromptVersionManager()
    pm.register(
        "v1.0",
        "你是客服助手。根据知识库回答用户问题。",
        "初始版本",
    )
    pm.register(
        "v1.1",
        "你是专业客服助手。语气友好，只根据知识库回答，不确定时说'建议联系人工客服'。",
        "优化语气+兜底策略",
    )
    print("\n✅ 注册了2个Prompt版本: v1.0, v1.1")

    # 2. 构建评估集
    evaluator = EvaluationRunner()
    evaluator.add_case(
        "退货流程怎么走？",
        ["退货", "寄回", "退款"],
        ["推荐", "购买"],
    )
    evaluator.add_case(
        "换货要多久？",
        ["换货", "天"],
        ["退货"],
    )
    evaluator.add_case(
        "投诉电话多少？",
        ["400", "客服"],
        [],
    )
    print(f"✅ 构建评估集: {len(evaluator.eval_set)} 条Case")

    # 3. 模拟生成函数
    def mock_generate_v1(question):
        return (
            f"根据知识库：关于'{question}'，"
            "退货需7天内寄回，换货15天内申请，投诉请拨400热线。"
        )

    def mock_generate_v2(question):
        return (
            f"您好！关于'{question}'，"
            "退货请在7天内寄回商品，我们收到后3个工作日退款。"
            "换货15天内可申请。如需投诉请拨400客服热线，24小时为您服务。"
        )

    # 4. 评估对比
    print("\n" + "-" * 60)
    print("📊 Prompt版本评估对比")
    print("-" * 60)

    r1 = evaluator.run(mock_generate_v1)
    print(f"\n  v1.0 评估结果: 通过率 {r1['pass_rate']:.0%} ({r1['passed']}/{r1['total']})")
    for d in r1["details"]:
        status = "✅" if d["pass"] else "❌"
        print(f"    {status} {d['question']} (关键词命中: {d['keyword_score']:.0%})")

    r2 = evaluator.run(mock_generate_v2)
    print(f"\n  v1.1 评估结果: 通过率 {r2['pass_rate']:.0%} ({r2['passed']}/{r2['total']})")
    for d in r2["details"]:
        status = "✅" if d["pass"] else "❌"
        print(f"    {status} {d['question']} (关键词命中: {d['keyword_score']:.0%})")

    # 5. 模拟灰度决策
    print("\n" + "-" * 60)
    print("🚦 灰度发布决策")
    print("-" * 60)
    threshold = 0.85
    if r2["pass_rate"] >= threshold:
        print(f"  v1.1 通过率 {r2['pass_rate']:.0%} >= {threshold:.0%}，允许灰度发布")
        pm.switch_active("v1.1")
    else:
        print(f"  v1.1 通过率 {r2['pass_rate']:.0%} < {threshold:.0%}，阻止上线")

    # 6. 模拟线上反馈
    print("\n" + "-" * 60)
    print("👥 模拟线上用户反馈")
    print("-" * 60)

    fc = FeedbackCollector()
    fc.collect("退货流程", "根据知识库...", "v1.0", False, "回答太生硬")
    fc.collect("换货要多久", "根据知识库...", "v1.0", True)
    fc.collect("退货流程", "您好！关于...", "v1.1", True)
    fc.collect("投诉电话", "您好！关于...", "v1.1", True)
    fc.collect("退款到账时间", "您好！关于...", "v1.1", False, "没有回答到账时间")

    summary = fc.summary()
    print(f"  总反馈: {summary['total_feedback']} 条")
    print(f"  满意率: {summary['satisfaction_rate']:.0%}")
    print(f"  正面: {summary['positive']} | 负面: {summary['negative']}")

    # 7. 反馈回流
    print("\n" + "-" * 60)
    print("🔄 反馈数据回流 → 评估集候选")
    print("-" * 60)

    candidates = fc.generate_eval_candidates()
    print(f"  从负面反馈中提取了 {len(candidates)} 条评估集候选:")
    for c in candidates:
        print(f"    📝 问题: {c['question']} | 用户吐槽: {c['user_comment']}")

    print("\n" + "=" * 60)
    print("✅ 迭代Pipeline演示完成")
    print("=" * 60)


if __name__ == "__main__":
    demo_iteration_pipeline()
