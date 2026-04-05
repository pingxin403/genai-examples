"""
RAG效果评估框架演示
==================
配套文章：《RAG效果怎么评估？召回率、忠实度、有用性全量化》

演示内容：
1. 检索质量评估（Hit Rate、MRR、NDCG）
2. 生成质量评估（忠实度、相关性、有用性）
3. 在线指标采集（用户采纳率、转人工率）
4. 完整评估管道编排 + 上线门槛检查
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


# ============================================================
# 第一部分：检索质量评估
# ============================================================

@dataclass
class RetrievalResult:
    query: str
    retrieved_doc_ids: list[str]   # 检索返回的文档ID（按相关性排序）
    relevant_doc_ids: list[str]    # 标注的正确文档ID


class RetrievalEvaluator:
    """检索质量评估器"""

    def hit_rate_at_k(self, results: list[RetrievalResult], k: int = 5) -> float:
        """Hit Rate@K: 正确文档出现在Top K中的查询占比"""
        hits = 0
        for r in results:
            top_k = set(r.retrieved_doc_ids[:k])
            if top_k & set(r.relevant_doc_ids):
                hits += 1
        return hits / len(results) if results else 0.0

    def mrr(self, results: list[RetrievalResult]) -> float:
        """MRR (Mean Reciprocal Rank): 正确文档排名倒数的平均值"""
        reciprocal_ranks = []
        for r in results:
            for rank, doc_id in enumerate(r.retrieved_doc_ids, 1):
                if doc_id in r.relevant_doc_ids:
                    reciprocal_ranks.append(1.0 / rank)
                    break
            else:
                reciprocal_ranks.append(0.0)
        return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0

    def ndcg_at_k(self, results: list[RetrievalResult], k: int = 5) -> float:
        """NDCG@K: 归一化折损累积增益"""
        ndcg_scores = []
        for r in results:
            dcg = 0.0
            for i, doc_id in enumerate(r.retrieved_doc_ids[:k]):
                if doc_id in r.relevant_doc_ids:
                    dcg += 1.0 / math.log2(i + 2)

            ideal_dcg = sum(
                1.0 / math.log2(i + 2)
                for i in range(min(len(r.relevant_doc_ids), k))
            )
            ndcg_scores.append(dcg / ideal_dcg if ideal_dcg > 0 else 0.0)

        return sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0


# ============================================================
# 第二部分：生成质量评估
# ============================================================

@dataclass
class GenerationResult:
    query: str
    answer: str
    retrieved_contexts: list[str]
    reference_answer: str = ""


class GenerationEvaluator:
    """生成质量评估器（基于规则的轻量版）"""

    def faithfulness_score(self, result: GenerationResult) -> float:
        """忠实度：回答中的关键信息是否能在检索内容中找到"""
        if not result.retrieved_contexts:
            return 0.0

        answer_sentences = [s.strip() for s in result.answer.split("。") if len(s.strip()) > 3]
        if not answer_sentences:
            return 1.0

        context_text = " ".join(result.retrieved_contexts)
        supported = 0
        for sentence in answer_sentences:
            # 简化版：检查句子中的关键片段是否在上下文中
            fragments = [f for f in sentence.split("，") if len(f) > 2]
            if any(frag in context_text for frag in fragments):
                supported += 1

        return supported / len(answer_sentences)

    def relevancy_score(self, result: GenerationResult) -> float:
        """相关性：回答是否切题（基于关键词重叠）"""
        query_tokens = set(result.query)
        answer_tokens = set(result.answer[:200])
        if not query_tokens:
            return 0.0
        overlap = query_tokens & answer_tokens
        return min(len(overlap) / len(query_tokens), 1.0)

    def usefulness_score(self, result: GenerationResult) -> float:
        """有用性：忠实度 × 0.6 + 相关性 × 0.4"""
        faith = self.faithfulness_score(result)
        relevancy = self.relevancy_score(result)
        return faith * 0.6 + relevancy * 0.4


# ============================================================
# 第三部分：在线指标采集
# ============================================================

@dataclass
class UserFeedback:
    query: str
    answer: str
    feedback_type: str  # "thumbs_up", "thumbs_down", "transfer_human"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    comment: str = ""


class OnlineMetricsCollector:
    """在线指标采集器"""

    def __init__(self):
        self.feedbacks: list[UserFeedback] = []

    def record_feedback(self, feedback: UserFeedback):
        self.feedbacks.append(feedback)

    def adoption_rate(self) -> float:
        """用户采纳率"""
        positive = sum(1 for f in self.feedbacks if f.feedback_type == "thumbs_up")
        negative = sum(1 for f in self.feedbacks if f.feedback_type == "thumbs_down")
        total = positive + negative
        return positive / total if total > 0 else 0.0

    def transfer_rate(self) -> float:
        """转人工率"""
        transfers = sum(1 for f in self.feedbacks if f.feedback_type == "transfer_human")
        return transfers / len(self.feedbacks) if self.feedbacks else 0.0

    def satisfaction_summary(self) -> dict:
        counts = defaultdict(int)
        for f in self.feedbacks:
            counts[f.feedback_type] += 1
        total = len(self.feedbacks)
        return {
            "total_interactions": total,
            "thumbs_up": counts["thumbs_up"],
            "thumbs_down": counts["thumbs_down"],
            "transfer_human": counts["transfer_human"],
            "adoption_rate": round(self.adoption_rate(), 4),
            "transfer_rate": round(self.transfer_rate(), 4),
        }


# ============================================================
# 第四部分：完整评估管道
# ============================================================

class RAGEvaluationPipeline:
    """RAG评估管道：离线评估 + 在线监控 + 门槛检查"""

    def __init__(self):
        self.retrieval_eval = RetrievalEvaluator()
        self.generation_eval = GenerationEvaluator()
        self.online_collector = OnlineMetricsCollector()

    def run_offline_eval(
        self,
        retrieval_results: list[RetrievalResult],
        generation_results: list[GenerationResult],
        k: int = 5,
    ) -> dict:
        hit_rate = self.retrieval_eval.hit_rate_at_k(retrieval_results, k)
        mrr = self.retrieval_eval.mrr(retrieval_results)
        ndcg = self.retrieval_eval.ndcg_at_k(retrieval_results, k)

        faith_scores = [self.generation_eval.faithfulness_score(r) for r in generation_results]
        relevancy_scores = [self.generation_eval.relevancy_score(r) for r in generation_results]
        useful_scores = [self.generation_eval.usefulness_score(r) for r in generation_results]

        avg = lambda lst: sum(lst) / len(lst) if lst else 0.0

        return {
            "retrieval": {
                "hit_rate@k": round(hit_rate, 4),
                "mrr": round(mrr, 4),
                "ndcg@k": round(ndcg, 4),
            },
            "generation": {
                "faithfulness": round(avg(faith_scores), 4),
                "relevancy": round(avg(relevancy_scores), 4),
                "usefulness": round(avg(useful_scores), 4),
            },
        }

    def check_thresholds(self, report: dict) -> list[str]:
        """检查上线门槛"""
        issues = []
        thresholds = {
            ("retrieval", "hit_rate@k"): 0.80,
            ("retrieval", "mrr"): 0.60,
            ("generation", "faithfulness"): 0.85,
            ("generation", "relevancy"): 0.80,
            ("generation", "usefulness"): 0.75,
        }
        for (category, metric), threshold in thresholds.items():
            value = report[category][metric]
            if value < threshold:
                issues.append(f"  ⚠️ {category}.{metric} = {value} < {threshold}")
        return issues


# ============================================================
# 演示入口
# ============================================================

def demo_retrieval_eval():
    """演示检索质量评估"""
    print("\n--- 1. 检索质量评估 ---")

    evaluator = RetrievalEvaluator()

    results = [
        RetrievalResult(
            query="年假天数怎么算",
            retrieved_doc_ids=["leave_policy", "attendance_rules", "hr_faq", "salary_guide", "onboarding"],
            relevant_doc_ids=["leave_policy"],
        ),
        RetrievalResult(
            query="报销流程是什么",
            retrieved_doc_ids=["travel_policy", "reimbursement", "finance_faq", "expense_guide", "hr_faq"],
            relevant_doc_ids=["reimbursement"],
        ),
        RetrievalResult(
            query="加班费怎么算",
            retrieved_doc_ids=["salary_guide", "overtime_policy", "hr_faq", "leave_policy", "attendance_rules"],
            relevant_doc_ids=["overtime_policy"],
        ),
        RetrievalResult(
            query="试用期多长",
            retrieved_doc_ids=["onboarding", "probation_policy", "hr_faq", "contract_template", "salary_guide"],
            relevant_doc_ids=["probation_policy"],
        ),
    ]

    print(f"  Hit Rate@3: {evaluator.hit_rate_at_k(results, k=3):.4f}")
    print(f"  Hit Rate@5: {evaluator.hit_rate_at_k(results, k=5):.4f}")
    print(f"  MRR:        {evaluator.mrr(results):.4f}")
    print(f"  NDCG@5:     {evaluator.ndcg_at_k(results, k=5):.4f}")


def demo_generation_eval():
    """演示生成质量评估"""
    print("\n--- 2. 生成质量评估 ---")

    evaluator = GenerationEvaluator()

    # 高忠实度案例
    good_result = GenerationResult(
        query="年假天数怎么算",
        answer="根据公司制度，工龄5年以下享有7天年假。工龄5年以上享有10天年假。",
        retrieved_contexts=["公司制度规定：工龄5年以下享有7天年假，工龄5年以上享有10天年假。"],
    )

    # 低忠实度案例（AI添加了检索内容中没有的信息）
    bad_result = GenerationResult(
        query="年假天数怎么算",
        answer="根据公司制度，工龄5年以下享有7天年假。年假可以累积到下一年使用，最多累积15天。",
        retrieved_contexts=["公司制度规定：工龄5年以下享有7天年假，工龄5年以上享有10天年假。"],
    )

    print(f"  高忠实度案例:")
    print(f"    忠实度: {evaluator.faithfulness_score(good_result):.4f}")
    print(f"    相关性: {evaluator.relevancy_score(good_result):.4f}")
    print(f"    有用性: {evaluator.usefulness_score(good_result):.4f}")

    print(f"  低忠实度案例:")
    print(f"    忠实度: {evaluator.faithfulness_score(bad_result):.4f}")
    print(f"    相关性: {evaluator.relevancy_score(bad_result):.4f}")
    print(f"    有用性: {evaluator.usefulness_score(bad_result):.4f}")


def demo_online_metrics():
    """演示在线指标采集"""
    print("\n--- 3. 在线指标采集 ---")

    collector = OnlineMetricsCollector()

    feedbacks = [
        UserFeedback(query="年假天数", answer="7天", feedback_type="thumbs_up"),
        UserFeedback(query="报销流程", answer="提交申请...", feedback_type="thumbs_up"),
        UserFeedback(query="加班费", answer="按1.5倍...", feedback_type="thumbs_up"),
        UserFeedback(query="请假扣钱吗", answer="不确定...", feedback_type="thumbs_down"),
        UserFeedback(query="合同在哪签", answer="请联系HR", feedback_type="transfer_human"),
        UserFeedback(query="社保基数", answer="按当地标准...", feedback_type="thumbs_up"),
        UserFeedback(query="离职流程", answer="提前30天...", feedback_type="thumbs_up"),
        UserFeedback(query="调岗申请", answer="...", feedback_type="thumbs_down"),
        UserFeedback(query="工资条在哪看", answer="...", feedback_type="transfer_human"),
        UserFeedback(query="培训报名", answer="登录系统...", feedback_type="thumbs_up"),
    ]

    for fb in feedbacks:
        collector.record_feedback(fb)

    summary = collector.satisfaction_summary()
    print(f"  总交互数:   {summary['total_interactions']}")
    print(f"  点赞:       {summary['thumbs_up']}")
    print(f"  点踩:       {summary['thumbs_down']}")
    print(f"  转人工:     {summary['transfer_human']}")
    print(f"  采纳率:     {summary['adoption_rate']:.4f}")
    print(f"  转人工率:   {summary['transfer_rate']:.4f}")


def demo_full_pipeline():
    """演示完整评估管道"""
    print("\n--- 4. 完整评估管道 ---")

    pipeline = RAGEvaluationPipeline()

    # 构造检索结果
    retrieval_results = [
        RetrievalResult("年假天数", ["leave_policy", "hr_faq", "salary"], ["leave_policy"]),
        RetrievalResult("报销流程", ["reimbursement", "finance", "hr_faq"], ["reimbursement"]),
        RetrievalResult("加班费", ["overtime", "salary", "hr_faq"], ["overtime"]),
        RetrievalResult("试用期", ["probation", "onboarding", "contract"], ["probation"]),
        RetrievalResult("社保基数", ["hr_faq", "social_insurance", "salary"], ["social_insurance"]),
    ]

    # 构造生成结果
    generation_results = [
        GenerationResult(
            "年假天数", "工龄5年以下享有7天年假",
            ["公司制度：工龄5年以下享有7天年假"],
        ),
        GenerationResult(
            "报销流程", "提交报销申请，附上发票，经理审批后财务打款",
            ["报销流程：提交申请，附发票，经理审批，财务打款"],
        ),
        GenerationResult(
            "加班费", "工作日加班按1.5倍工资计算，周末按2倍",
            ["加班费标准：工作日1.5倍，周末2倍，法定假日3倍"],
        ),
        GenerationResult(
            "试用期", "试用期为3个月，表现优秀可提前转正",
            ["试用期规定：标准试用期3个月"],
        ),
        GenerationResult(
            "社保基数", "按当地上年度平均工资的60%-300%确定",
            ["社保缴费基数：按当地上年度平均工资的60%-300%"],
        ),
    ]

    # 运行离线评估
    report = pipeline.run_offline_eval(retrieval_results, generation_results, k=3)

    print("  离线评估报告:")
    print(f"    检索指标:")
    for metric, value in report["retrieval"].items():
        print(f"      {metric}: {value}")
    print(f"    生成指标:")
    for metric, value in report["generation"].items():
        print(f"      {metric}: {value}")

    # 检查上线门槛
    issues = pipeline.check_thresholds(report)
    if issues:
        print("\n  ⚠️ 以下指标未达标:")
        for issue in issues:
            print(issue)
    else:
        print("\n  ✅ 所有指标达标，可以上线！")


if __name__ == "__main__":
    print("=== RAG评估框架演示 ===")
    demo_retrieval_eval()
    demo_generation_eval()
    demo_online_metrics()
    demo_full_pipeline()
    print("\n=== 演示完成 ===")
