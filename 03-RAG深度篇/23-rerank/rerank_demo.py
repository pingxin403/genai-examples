"""
Rerank精排示例 - 三种策略演示
配套文章：《Rerank精排：如何把Top 100变Top 10还不掉精度？》

演示内容：
1. Cross-Encoder精排：用交叉编码器对候选文档重新排序
2. 业务规则融合：语义分数 + 部门/时效性/文档类型
3. 分级Rerank：快速/标准/精确三种模式的延迟-精度权衡
"""

import time
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta


# ============================================================
# 模拟数据
# ============================================================

SAMPLE_DOCUMENTS = [
    "员工年假天数根据工龄计算，5年以下5天，5-10年10天，10年以上15天",
    "病假需要提供医院证明，超过3天需部门经理审批",
    "调休需在加班后30天内申请，逾期作废",
    "年假申请流程：OA系统提交→直属领导审批→HR备案",
    "离职时未休年假按日薪折算补偿",
    "婚假标准为3天，晚婚可增加7天",
    "产假标准为98天，难产增加15天",
    "丧假直系亲属3天，非直系亲属1天",
    "北京办公室考勤时间为9:00-18:00",
    "上海办公室考勤时间为9:30-18:30",
    "深圳办公室实行弹性工作制，核心时间10:00-16:00",
    "报销流程：填写报销单→部门审批→财务审核→打款",
    "差旅标准：经济舱/高铁二等座，酒店不超过500元/晚",
    "新员工入职需要提交身份证、学历证、离职证明",
    "试用期考核标准包括工作能力、团队协作、学习态度三个维度",
]


@dataclass
class RichDocument:
    """带业务属性的文档"""
    content: str
    dept: str
    updated_at: str
    doc_type: str  # policy / faq / guide


RICH_DOCUMENTS = [
    RichDocument("员工年假天数根据工龄计算，5年以下5天，5-10年10天", "hr",
                 (datetime.now() - timedelta(days=30)).isoformat(), "policy"),
    RichDocument("年假申请流程：OA系统提交→直属领导审批→HR备案", "hr",
                 (datetime.now() - timedelta(days=10)).isoformat(), "guide"),
    RichDocument("病假需要提供医院证明，超过3天需部门经理审批", "hr",
                 (datetime.now() - timedelta(days=200)).isoformat(), "policy"),
    RichDocument("北京办公室考勤时间为9:00-18:00", "admin",
                 (datetime.now() - timedelta(days=365)).isoformat(), "faq"),
    RichDocument("报销流程：填写报销单→部门审批→财务审核→打款", "finance",
                 (datetime.now() - timedelta(days=60)).isoformat(), "guide"),
]


# ============================================================
# 策略1: Cross-Encoder精排（模拟版，无需GPU）
# ============================================================

class SimulatedCrossEncoder:
    """
    模拟Cross-Encoder的行为。
    生产环境请替换为:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder("BAAI/bge-reranker-v2-m3")
    """

    def predict(self, pairs: list[list[str]]) -> np.ndarray:
        """模拟Cross-Encoder打分：基于关键词重叠 + 语义启发式"""
        scores = []
        for query, doc in pairs:
            query_chars = set(query)
            doc_chars = set(doc)
            # 字符重叠率作为模拟分数
            overlap = len(query_chars & doc_chars) / max(len(query_chars), 1)
            # 加入一些随机性模拟模型行为
            noise = np.random.normal(0, 0.05)
            score = np.clip(overlap + noise, -1, 1)
            scores.append(score)
        return np.array(scores)


def demo_cross_encoder_rerank():
    """演示Cross-Encoder精排"""
    print("=" * 60)
    print("Demo 1: Cross-Encoder精排")
    print("=" * 60)

    reranker = SimulatedCrossEncoder()
    query = "年假怎么请"

    print(f"Query: {query}")
    print(f"候选文档数: {len(SAMPLE_DOCUMENTS)}")
    print()

    # 构造query-document对
    pairs = [[query, doc] for doc in SAMPLE_DOCUMENTS]

    # 模型打分
    start = time.time()
    scores = reranker.predict(pairs)
    latency = (time.time() - start) * 1000

    # 按分数降序排列
    ranked_indices = np.argsort(scores)[::-1]

    print("精排结果 (Top 5):")
    for rank, idx in enumerate(ranked_indices[:5]):
        print(f"  #{rank + 1} [score: {scores[idx]:.2f}] {SAMPLE_DOCUMENTS[idx]}")

    print(f"\n精排延迟: {latency:.1f}ms")
    print()


# ============================================================
# 策略2: 业务规则融合
# ============================================================

def business_rule_rerank(
    query: str,
    documents: list[RichDocument],
    user_dept: str,
    semantic_scores: list[float],
    weights: dict = None,
) -> list[dict]:
    """融合语义分数 + 业务规则的综合排序"""
    if weights is None:
        weights = {
            "semantic": 0.6,
            "freshness": 0.2,
            "dept_match": 0.15,
            "type_boost": 0.05,
        }

    results = []
    now = datetime.now()

    for doc, sem_score in zip(documents, semantic_scores):
        # 1. 语义分数归一化到0-1
        normalized_semantic = (sem_score + 1) / 2

        # 2. 时效性分数（越新越高）
        doc_date = datetime.fromisoformat(doc.updated_at)
        days_old = (now - doc_date).days
        freshness_score = max(0, 1 - days_old / 365)

        # 3. 部门匹配分数
        dept_score = 1.0 if doc.dept == user_dept else 0.3

        # 4. 文档类型加权
        type_scores = {"policy": 1.0, "faq": 0.8, "guide": 0.6}
        type_score = type_scores.get(doc.doc_type, 0.5)

        # 综合分数
        final_score = (
            weights["semantic"] * normalized_semantic
            + weights["freshness"] * freshness_score
            + weights["dept_match"] * dept_score
            + weights["type_boost"] * type_score
        )

        results.append({
            "content": doc.content,
            "dept": doc.dept,
            "doc_type": doc.doc_type,
            "semantic_score": round(sem_score, 3),
            "freshness_score": round(freshness_score, 3),
            "dept_match": doc.dept == user_dept,
            "final_score": round(final_score, 3),
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results


def demo_business_rule_rerank():
    """演示业务规则融合排序"""
    print("=" * 60)
    print("Demo 2: 业务规则融合排序")
    print("=" * 60)

    query = "年假怎么请"
    user_dept = "hr"

    # 模拟Cross-Encoder的语义分数
    semantic_scores = [0.85, 0.90, 0.40, 0.10, 0.20]

    print(f"Query: {query}")
    print(f"用户部门: {user_dept}")
    print(f"权重: semantic=0.6, freshness=0.2, dept_match=0.15, type_boost=0.05")
    print()

    results = business_rule_rerank(query, RICH_DOCUMENTS, user_dept, semantic_scores)

    print("融合排序结果:")
    for i, r in enumerate(results):
        print(f"  #{i + 1} [综合: {r['final_score']:.3f}] "
              f"[语义: {r['semantic_score']:.2f}] "
              f"[时效: {r['freshness_score']:.2f}] "
              f"[部门匹配: {'✓' if r['dept_match'] else '✗'}] "
              f"({r['doc_type']}) {r['content'][:40]}...")
    print()


# ============================================================
# 策略3: 分级Rerank（延迟-精度权衡）
# ============================================================

class TieredReranker:
    """三级精排策略：快速 / 标准 / 精确"""

    def __init__(self):
        self.cross_encoder = SimulatedCrossEncoder()

    def rerank(self, query: str, documents: list[str],
               mode: str = "standard", top_k: int = 5) -> dict:
        start = time.time()

        if mode == "fast":
            results = self._keyword_rerank(query, documents, top_k)
        elif mode == "standard":
            candidates = documents[:50]  # 只精排前50条
            results = self._cross_encoder_rerank(query, candidates, top_k)
        elif mode == "precise":
            results = self._cross_encoder_rerank(query, documents, top_k)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        latency = (time.time() - start) * 1000
        return {"results": results, "latency_ms": round(latency, 2), "mode": mode}

    def _keyword_rerank(self, query, documents, top_k):
        """基于关键词重叠度的快速重排"""
        query_chars = set(query)
        scored = []
        for doc in documents:
            doc_chars = set(doc)
            overlap = len(query_chars & doc_chars) / max(len(query_chars), 1)
            scored.append({"document": doc, "score": round(overlap, 3)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _cross_encoder_rerank(self, query, documents, top_k):
        """Cross-Encoder精排"""
        pairs = [[query, doc] for doc in documents]
        scores = self.cross_encoder.predict(pairs)
        combined = list(zip(documents, scores))
        combined.sort(key=lambda x: x[1], reverse=True)
        return [{"document": d, "score": round(float(s), 3)}
                for d, s in combined[:top_k]]


def demo_tiered_rerank():
    """演示分级Rerank的延迟-精度权衡"""
    print("=" * 60)
    print("Demo 3: 分级Rerank延迟对比")
    print("=" * 60)

    reranker = TieredReranker()
    query = "年假怎么请"

    print(f"Query: {query}")
    print(f"候选文档数: {len(SAMPLE_DOCUMENTS)}")
    print()

    for mode in ["fast", "standard", "precise"]:
        result = reranker.rerank(query, SAMPLE_DOCUMENTS, mode=mode, top_k=3)
        print(f"  [{mode:10s}] 延迟: {result['latency_ms']:>8.2f}ms")
        for i, r in enumerate(result["results"]):
            print(f"    #{i + 1} [score: {r['score']:.3f}] {r['document'][:50]}...")
        print()


# ============================================================
# 延迟-精度权衡分析
# ============================================================

def demo_latency_accuracy_tradeoff():
    """演示不同候选数量对延迟的影响"""
    print("=" * 60)
    print("Demo 4: 候选数量 vs 精排延迟")
    print("=" * 60)

    reranker = SimulatedCrossEncoder()
    query = "年假怎么请"

    # 模拟不同规模的候选集
    candidate_sizes = [10, 50, 100, 200, 500]

    print(f"{'候选数量':>10s} | {'延迟(ms)':>10s} | {'建议'}")
    print("-" * 50)

    for size in candidate_sizes:
        # 复制文档到目标数量
        docs = (SAMPLE_DOCUMENTS * (size // len(SAMPLE_DOCUMENTS) + 1))[:size]
        pairs = [[query, doc] for doc in docs]

        start = time.time()
        _ = reranker.predict(pairs)
        latency = (time.time() - start) * 1000

        if latency < 50:
            suggestion = "✅ 推荐"
        elif latency < 200:
            suggestion = "⚠️ 可接受"
        else:
            suggestion = "❌ 过慢"

        print(f"{size:>10d} | {latency:>10.1f} | {suggestion}")

    print()


# ============================================================
# 主函数
# ============================================================

def main():
    print()
    print("🧠 Rerank精排策略演示")
    print("=" * 60)
    print()

    demo_cross_encoder_rerank()
    demo_business_rule_rerank()
    demo_tiered_rerank()
    demo_latency_accuracy_tradeoff()

    print("=" * 60)
    print("演示完成！")
    print()
    print("生产环境建议：")
    print("  1. 将 SimulatedCrossEncoder 替换为真实模型:")
    print("     from sentence_transformers import CrossEncoder")
    print('     model = CrossEncoder("BAAI/bge-reranker-v2-m3")')
    print("  2. 粗排取Top 50-200条给精排")
    print("  3. 融合业务规则（部门、时效性、文档类型）")
    print("  4. 根据延迟预算选择分级策略")
    print()


if __name__ == "__main__":
    main()
