"""
Embedding模型横向评测实战演示
配套文章：《Embedding模型怎么选？7款主流模型横向评测》

演示内容：
1. 7款主流Embedding模型参数对比
2. 基于Hit Rate / MRR的检索质量评测框架
3. 向量存储成本估算
4. 多领域评测与选型建议
"""

import time
import numpy as np


# ============================================================
# 7款主流Embedding模型配置
# ============================================================

MODELS = {
    "BGE-large-zh": {
        "vendor": "BAAI(智源)",
        "dim": 1024,
        "max_tokens": 512,
        "chinese": "原生支持",
        "open_source": True,
        "deploy": "本地部署",
    },
    "text-embedding-3-small": {
        "vendor": "OpenAI",
        "dim": 1536,
        "max_tokens": 8191,
        "chinese": "良好",
        "open_source": False,
        "deploy": "API调用",
    },
    "text-embedding-3-large": {
        "vendor": "OpenAI",
        "dim": 3072,
        "max_tokens": 8191,
        "chinese": "良好",
        "open_source": False,
        "deploy": "API调用",
    },
    "E5-large-v2": {
        "vendor": "Microsoft",
        "dim": 1024,
        "max_tokens": 512,
        "chinese": "一般",
        "open_source": True,
        "deploy": "本地部署",
    },
    "GTE-large-zh": {
        "vendor": "阿里达摩院",
        "dim": 1024,
        "max_tokens": 512,
        "chinese": "原生支持",
        "open_source": True,
        "deploy": "本地部署",
    },
    "Cohere-embed-v3": {
        "vendor": "Cohere",
        "dim": 1024,
        "max_tokens": 512,
        "chinese": "良好",
        "open_source": False,
        "deploy": "API调用",
    },
    "Jina-embeddings-v2": {
        "vendor": "Jina AI",
        "dim": 768,
        "max_tokens": 8192,
        "chinese": "良好",
        "open_source": True,
        "deploy": "API/本地",
    },
}


# ============================================================
# Embedding评测框架
# ============================================================

class EmbeddingEvaluator:
    """Embedding模型横向评测器"""

    def __init__(self):
        self.results = {}

    def evaluate_model(self, model_name: str, embed_fn,
                       queries: list[str], corpus: list[str],
                       ground_truth: list[list[int]],
                       top_k: int = 5) -> dict:
        """
        评测单个Embedding模型的检索质量
        - embed_fn: 接收文本列表，返回向量列表
        - ground_truth: 每个query对应的正确文档索引
        """
        # 1. 向量化并计时
        start = time.time()
        corpus_embeddings = embed_fn(corpus)
        encode_time = time.time() - start

        query_embeddings = embed_fn(queries)

        # 2. 检索并计算指标
        hit_count = 0
        mrr_sum = 0.0

        for i, q_emb in enumerate(query_embeddings):
            # 计算query与所有文档的余弦相似度
            scores = [self._cosine_sim(q_emb, c_emb)
                      for c_emb in corpus_embeddings]
            top_indices = np.argsort(scores)[::-1][:top_k]

            # Hit Rate: 正确文档是否出现在Top-K结果中
            if any(idx in ground_truth[i] for idx in top_indices):
                hit_count += 1

            # MRR: 第一个正确文档的排名倒数
            for rank, idx in enumerate(top_indices):
                if idx in ground_truth[i]:
                    mrr_sum += 1.0 / (rank + 1)
                    break

        result = {
            "model": model_name,
            "hit_rate": round(hit_count / len(queries), 3),
            "mrr": round(mrr_sum / len(queries), 3),
            "encode_time_sec": round(encode_time, 4),
            "dimension": len(corpus_embeddings[0]),
            "throughput_per_sec": round(len(corpus) / max(encode_time, 0.001), 1),
        }
        self.results[model_name] = result
        return result

    @staticmethod
    def _cosine_sim(a, b) -> float:
        a_arr, b_arr = np.array(a), np.array(b)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


# ============================================================
# 模拟Embedding函数（实际项目中替换为真实模型调用）
# ============================================================

def make_embed_fn(dim: int, seed_offset: int = 0):
    """创建模拟embedding函数"""
    def embed_fn(texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            np.random.seed((hash(text) + seed_offset) % (2**32))
            vec = np.random.rand(dim).astype(np.float32)
            vec = vec / np.linalg.norm(vec)  # L2归一化
            results.append(vec.tolist())
        return results
    return embed_fn


# ============================================================
# 存储成本估算
# ============================================================

def estimate_storage(num_chunks: int, dim: int,
                     bytes_per_float: int = 4) -> dict:
    """估算向量存储开销"""
    total_bytes = num_chunks * dim * bytes_per_float
    return {
        "num_chunks": num_chunks,
        "dimension": dim,
        "total_mb": round(total_bytes / (1024**2), 1),
        "total_gb": round(total_bytes / (1024**3), 2),
    }


# ============================================================
# 演示主程序
# ============================================================

def main():
    print("=" * 65)
    print("🎯 Embedding模型横向评测演示")
    print("=" * 65)

    # --- 1. 模型参数对比 ---
    print("\n📌 1. 7款主流Embedding模型参数对比")
    print("-" * 65)
    print(f"{'模型':<26} {'厂商':<12} {'维度':<6} {'中文':<8} {'开源':<6}")
    print("-" * 65)
    for name, info in MODELS.items():
        oss = "✅" if info["open_source"] else "❌"
        print(f"{name:<26} {info['vendor']:<12} {info['dim']:<6} "
              f"{info['chinese']:<8} {oss:<6}")

    # --- 2. 构造评测数据集 ---
    print("\n📌 2. 构造评测数据集")
    print("-" * 65)

    queries = [
        "合同违约责任如何认定",
        "Python异步编程怎么实现",
        "RAG系统检索优化方法",
        "糖尿病的饮食注意事项",
        "商品退货流程是什么",
    ]

    corpus = [
        "合同违约责任的认定需要考虑违约行为、损害结果和因果关系三个要素",
        "合同签订流程包括要约、承诺、签字盖章三个步骤",
        "Python的asyncio库提供了异步编程的核心支持，包括事件循环和协程",
        "Java的多线程编程通过Thread类和Runnable接口实现",
        "RAG系统通过向量检索召回相关文档，再交给LLM生成回答",
        "传统搜索引擎主要依赖倒排索引和BM25算法进行关键词匹配",
        "糖尿病患者应控制碳水化合物摄入，多吃蔬菜，少吃高糖食物",
        "高血压患者需要限制钠盐摄入，每日不超过6克",
        "商品退货需要在签收后7天内申请，保持商品完好并提供购买凭证",
        "商品换货流程与退货类似，但需要选择替换的商品规格",
    ]

    ground_truth = [[0], [2], [4], [6], [8]]

    print(f"  查询数量: {len(queries)}")
    print(f"  文档数量: {len(corpus)}")
    print(f"  示例查询: '{queries[0]}'")
    print(f"  对应文档: '{corpus[ground_truth[0][0]][:40]}...'")

    # --- 3. 多模型评测 ---
    print("\n📌 3. 多模型检索质量评测 (Top-5)")
    print("-" * 65)

    evaluator = EmbeddingEvaluator()
    seed_offsets = [0, 100, 200, 300, 400, 500, 600]

    for i, (model_name, config) in enumerate(MODELS.items()):
        embed_fn = make_embed_fn(config["dim"], seed_offsets[i])
        result = evaluator.evaluate_model(
            model_name, embed_fn, queries, corpus, ground_truth
        )
        print(f"  {model_name:<26} Hit Rate={result['hit_rate']:.2f}  "
              f"MRR={result['mrr']:.2f}  Dim={result['dimension']}")

    # --- 4. 存储成本估算 ---
    print("\n📌 4. 向量存储成本估算（50万条chunk）")
    print("-" * 65)
    num_chunks = 500_000
    print(f"{'模型':<26} {'维度':<8} {'存储(MB)':<12} {'存储(GB)':<10}")
    print("-" * 55)
    for name, config in MODELS.items():
        storage = estimate_storage(num_chunks, config["dim"])
        print(f"{name:<26} {config['dim']:<8} "
              f"{storage['total_mb']:<12} {storage['total_gb']:<10}")

    # --- 5. 选型建议 ---
    print("\n📌 5. 选型建议")
    print("-" * 65)
    recommendations = [
        ("中文领域（法律/金融）", "BGE-large-zh",
         "原生中文训练，领域语义区分度高，支持微调"),
        ("通用场景（预算充足）", "text-embedding-3-large",
         "综合效果好，支持维度缩减，长文本支持8K tokens"),
        ("通用场景（性价比）", "text-embedding-3-small",
         "效果与large差距3-4%，维度和成本减半"),
        ("本地部署（数据合规）", "GTE-large-zh",
         "开源免费，中文效果好，无数据外传风险"),
        ("多语言场景", "Cohere-embed-v3",
         "多语言支持好，API稳定，1024维平衡效果与成本"),
    ]
    for scenario, model, reason in recommendations:
        print(f"  🎯 {scenario}")
        print(f"     推荐: {model}")
        print(f"     理由: {reason}\n")

    print("=" * 65)
    print("✅ 评测完成！实际项目中请替换模拟embedding为真实模型调用")
    print("=" * 65)


if __name__ == "__main__":
    main()
