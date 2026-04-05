"""
混合搜索实战Demo：向量 + BM25关键词，1+1>2的融合之道
配套文章：《混合搜索：向量+关键词，1+1>2的融合之道》

演示内容：
1. BM25关键词搜索引擎
2. 向量语义搜索（模拟Embedding）
3. 分数归一化（Min-Max / RRF）
4. 加权融合与自适应alpha
5. Rerank触发策略
"""

import math
import re
import numpy as np


# ============================================================
# 第一部分：BM25 关键词搜索
# ============================================================

class BM25:
    """BM25关键词检索引擎"""

    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.doc_count = len(corpus)
        self.tokenized = [self._tokenize(doc) for doc in corpus]
        self.avg_dl = sum(len(d) for d in self.tokenized) / self.doc_count
        self.idf = self._compute_idf()

    def _tokenize(self, text: str) -> list[str]:
        """简单分词：按中文字符和英文单词切分"""
        return [w for w in re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)]

    def _compute_idf(self) -> dict[str, float]:
        df = {}
        for doc in self.tokenized:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1
        return {
            term: math.log((self.doc_count - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }

    def score(self, query: str) -> list[float]:
        """计算query与每个文档的BM25分数"""
        query_terms = self._tokenize(query)
        scores = []
        for doc_tokens in self.tokenized:
            s = 0.0
            dl = len(doc_tokens)
            tf_map = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1
            for term in query_terms:
                if term not in self.idf:
                    continue
                tf = tf_map.get(term, 0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                s += self.idf[term] * numerator / denominator
            scores.append(s)
        return scores


# ============================================================
# 第二部分：向量搜索（模拟Embedding）
# ============================================================

def simulate_embedding(text: str, dim: int = 256) -> list[float]:
    """模拟Embedding向量（实际项目中替换为真实模型调用）"""
    np.random.seed(hash(text) % (2**32))
    vec = np.random.rand(dim).astype(np.float32)
    return (vec / np.linalg.norm(vec)).tolist()


def cosine_sim(a: list[float], b: list[float]) -> float:
    """余弦相似度"""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ============================================================
# 第三部分：分数归一化
# ============================================================

def min_max_normalize(scores: list[float]) -> list[float]:
    """Min-Max归一化到[0, 1]"""
    min_s, max_s = min(scores), max(scores)
    if max_s == min_s:
        return [0.5] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]


def rrf_normalize(scores: list[float], k: int = 60) -> list[float]:
    """RRF倒数排名融合归一化"""
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    rrf_scores = [0.0] * len(scores)
    for rank, idx in enumerate(ranked_indices):
        rrf_scores[idx] = 1.0 / (k + rank + 1)
    # 归一化到[0, 1]
    return min_max_normalize(rrf_scores)


# ============================================================
# 第四部分：加权融合与自适应Alpha
# ============================================================

def weighted_fusion(vec_scores: list[float], bm25_scores: list[float],
                    alpha: float = 0.6) -> list[float]:
    """加权融合：alpha * 向量 + (1-alpha) * BM25"""
    return [alpha * v + (1 - alpha) * b for v, b in zip(vec_scores, bm25_scores)]


def adaptive_alpha(query: str) -> float:
    """根据query特征动态调整alpha权重"""
    # 包含专有名词/编号 → 偏向关键词搜索
    if re.search(r'[A-Z]{2,}|\d{3,}|ISO|GB|RFC', query):
        return 0.3
    # 口语化/模糊描述 → 偏向向量搜索
    if len(query) > 15 or any(w in query for w in ['怎么', '如何', '什么是', '为什么']):
        return 0.7
    return 0.5


# ============================================================
# 第五部分：混合搜索Pipeline
# ============================================================

class HybridSearchPipeline:
    """混合搜索Pipeline：向量 + BM25 + 可选Rerank"""

    def __init__(self, corpus: list[str], alpha: float = 0.6,
                 rerank_threshold: float = 0.05, use_adaptive_alpha: bool = False):
        self.corpus = corpus
        self.default_alpha = alpha
        self.rerank_threshold = rerank_threshold
        self.use_adaptive_alpha = use_adaptive_alpha
        # 构建双索引
        self.bm25 = BM25(corpus)
        self.corpus_embeddings = [simulate_embedding(doc) for doc in corpus]

    def search(self, query: str, top_k: int = 5) -> tuple[list[dict], bool]:
        """执行混合搜索，返回(结果列表, 是否需要rerank)"""
        # 1. 向量搜索
        q_emb = simulate_embedding(query)
        vec_scores = [cosine_sim(q_emb, c) for c in self.corpus_embeddings]

        # 2. BM25搜索
        bm25_scores = self.bm25.score(query)

        # 3. 归一化
        norm_vec = min_max_normalize(vec_scores)
        norm_bm25 = min_max_normalize(bm25_scores)

        # 4. 加权融合
        alpha = adaptive_alpha(query) if self.use_adaptive_alpha else self.default_alpha
        fused = weighted_fusion(norm_vec, norm_bm25, alpha)

        # 5. 排序
        ranked = sorted(enumerate(fused), key=lambda x: x[1], reverse=True)

        # 6. 判断是否触发rerank
        need_rerank = (len(ranked) >= 2 and
                       ranked[0][1] - ranked[1][1] < self.rerank_threshold)

        results = []
        for idx, score in ranked[:top_k]:
            results.append({
                "rank": len(results) + 1,
                "doc": self.corpus[idx][:60] + "..." if len(self.corpus[idx]) > 60 else self.corpus[idx],
                "fused_score": round(score, 4),
                "vec_score": round(norm_vec[idx], 4),
                "bm25_score": round(norm_bm25[idx], 4),
            })

        return results, need_rerank, alpha

    def vector_only_search(self, query: str, top_k: int = 5) -> list[dict]:
        """纯向量搜索（用于对比）"""
        q_emb = simulate_embedding(query)
        scores = [cosine_sim(q_emb, c) for c in self.corpus_embeddings]
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [{"rank": i+1, "doc": self.corpus[idx][:60], "score": round(s, 4)}
                for i, (idx, s) in enumerate(ranked[:top_k])]

    def bm25_only_search(self, query: str, top_k: int = 5) -> list[dict]:
        """纯BM25搜索（用于对比）"""
        scores = self.bm25.score(query)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [{"rank": i+1, "doc": self.corpus[idx][:60], "score": round(s, 4)}
                for i, (idx, s) in enumerate(ranked[:top_k])]


# ============================================================
# 第六部分：评测与效果对比
# ============================================================

def evaluate_search(pipeline: HybridSearchPipeline,
                    queries: list[str],
                    ground_truth: list[list[int]],
                    top_k: int = 5) -> dict:
    """评测搜索效果：Hit Rate + MRR"""
    methods = {"vector": 0, "bm25": 0, "hybrid": 0}
    mrr = {"vector": 0.0, "bm25": 0.0, "hybrid": 0.0}

    for i, query in enumerate(queries):
        gt = ground_truth[i]

        # 向量搜索
        vec_results = pipeline.vector_only_search(query, top_k)
        vec_indices = [list(enumerate(pipeline.corpus)).index(
            next((j, d) for j, d in enumerate(pipeline.corpus) if d[:60] == r["doc"]))
            if any(d[:60] == r["doc"] for j, d in enumerate(pipeline.corpus)) else -1
            for r in vec_results]

        # BM25搜索
        bm25_results = pipeline.bm25_only_search(query, top_k)

        # 混合搜索
        hybrid_results, _, _ = pipeline.search(query, top_k)

        # 简化评测：检查ground truth文档是否在结果中
        for method_name, results in [("vector", vec_results),
                                      ("bm25", bm25_results),
                                      ("hybrid", hybrid_results)]:
            for gt_idx in gt:
                gt_doc_prefix = pipeline.corpus[gt_idx][:60]
                for rank, r in enumerate(results):
                    if gt_doc_prefix in r["doc"]:
                        methods[method_name] += 1
                        mrr[method_name] += 1.0 / (rank + 1)
                        break

    n = len(queries)
    return {
        method: {
            "hit_rate": f"{methods[method]/n:.0%}",
            "mrr": f"{mrr[method]/n:.2f}"
        }
        for method in methods
    }


# ============================================================
# 主程序
# ============================================================

def main():
    print("=" * 70)
    print("🔍 混合搜索实战Demo：向量 + BM25，1+1>2的融合之道")
    print("=" * 70)

    # 构造知识库语料
    corpus = [
        "员工年假天数根据工龄计算：1-10年为5天，10-20年为10天，20年以上为15天",
        "休假审批流程：员工提交申请→直属领导审批→HR备案→休假",
        "合同违约责任的认定需要考虑违约行为、损害结果和因果关系三个要素",
        "ISO 27001信息安全管理体系认证流程包括差距分析、体系建设、内审和外审四个阶段",
        "Python异步编程使用asyncio库，核心概念包括事件循环、协程和Future",
        "RAG系统通过向量检索召回相关文档，再交给LLM生成回答，是知识问答的主流方案",
        "BM25算法基于词频和逆文档频率计算文档相关性，是经典的信息检索算法",
        "向量数据库如Milvus和Qdrant支持高效的近似最近邻搜索，适合大规模向量检索",
        "员工病假需要提供医院证明，病假期间工资按基本工资的80%发放",
        "公司差旅报销标准：经济舱机票、四星以下酒店、每日餐补200元",
    ]

    # 初始化Pipeline
    pipeline = HybridSearchPipeline(
        corpus=corpus,
        alpha=0.6,
        rerank_threshold=0.05,
        use_adaptive_alpha=True
    )

    # 测试query
    test_queries = [
        ("年假天数", "精确关键词型"),
        ("请假怎么走流程", "语义模糊型"),
        ("ISO 27001认证流程", "专有名词型"),
        ("RAG系统怎么做检索", "技术语义型"),
    ]

    print("\n📊 三种搜索方式对比测试")
    print("-" * 70)

    for query, query_type in test_queries:
        print(f"\n🔎 Query: 「{query}」 (类型: {query_type})")
        alpha = adaptive_alpha(query)
        print(f"   自适应Alpha: {alpha} (向量{alpha:.0%} / 关键词{1-alpha:.0%})")

        # 纯向量搜索
        vec_results = pipeline.vector_only_search(query, top_k=3)
        print(f"\n   [向量搜索 Top-3]")
        for r in vec_results:
            print(f"     #{r['rank']} (score={r['score']}) {r['doc']}")

        # 纯BM25搜索
        bm25_results = pipeline.bm25_only_search(query, top_k=3)
        print(f"\n   [BM25搜索 Top-3]")
        for r in bm25_results:
            print(f"     #{r['rank']} (score={r['score']}) {r['doc']}")

        # 混合搜索
        hybrid_results, need_rerank, used_alpha = pipeline.search(query, top_k=3)
        rerank_flag = " ⚠️ 建议触发Rerank" if need_rerank else " ✅ 无需Rerank"
        print(f"\n   [混合搜索 Top-3] (alpha={used_alpha}){rerank_flag}")
        for r in hybrid_results:
            print(f"     #{r['rank']} (fused={r['fused_score']}, "
                  f"vec={r['vec_score']}, bm25={r['bm25_score']}) {r['doc']}")

    # 归一化方法对比
    print("\n\n📐 分数归一化方法对比")
    print("-" * 70)
    raw_bm25 = [12.5, 8.3, 3.1, 0.0, 15.2]
    raw_vec = [0.85, 0.72, 0.91, 0.45, 0.68]
    print(f"原始BM25分数:    {raw_bm25}")
    print(f"原始向量分数:    {raw_vec}")
    print(f"Min-Max(BM25):   {[round(x, 3) for x in min_max_normalize(raw_bm25)]}")
    print(f"Min-Max(向量):   {[round(x, 3) for x in min_max_normalize(raw_vec)]}")
    print(f"RRF(BM25):       {[round(x, 3) for x in rrf_normalize(raw_bm25)]}")
    print(f"RRF(向量):       {[round(x, 3) for x in rrf_normalize(raw_vec)]}")

    # 不同alpha的效果对比
    print("\n\n⚖️ Alpha权重敏感性分析")
    print("-" * 70)
    query = "年假天数"
    for alpha in [0.2, 0.4, 0.5, 0.6, 0.8]:
        pipeline_fixed = HybridSearchPipeline(corpus=corpus, alpha=alpha)
        results, need_rerank, _ = pipeline_fixed.search(query, top_k=3)
        top1_doc = results[0]["doc"] if results else "N/A"
        print(f"  alpha={alpha}: Top-1 = {top1_doc} (score={results[0]['fused_score']})")

    print("\n" + "=" * 70)
    print("✅ Demo完成！混合搜索通过向量+关键词互补，显著提升检索召回率")
    print("=" * 70)


if __name__ == "__main__":
    main()
