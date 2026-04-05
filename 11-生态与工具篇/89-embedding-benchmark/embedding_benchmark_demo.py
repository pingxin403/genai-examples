"""
Embedding模型评测演示：7款模型在5个领域的表现
模拟评测框架，展示Hit Rate / MRR / 成本对比
"""

import math
import time
from dataclasses import dataclass, field


# ============================================================
# 数据结构
# ============================================================
@dataclass
class EmbeddingModel:
    name: str
    dimension: int
    max_tokens: int
    cost_per_million: float  # $/百万Token
    chinese_native: bool = False


@dataclass
class EvalDataset:
    domain: str
    queries: list[str]
    documents: list[str]
    relevance: dict  # {query_idx: [relevant_doc_indices]}


@dataclass
class EvalResult:
    model: str
    domain: str
    hit_rate: float
    mrr: float
    avg_latency_ms: float
    cost_per_query: float


# ============================================================
# 评测引擎
# ============================================================
class EmbeddingBenchmark:
    def __init__(self):
        self.models = [
            EmbeddingModel("text-embedding-3-large", 3072, 8191, 0.13),
            EmbeddingModel("text-embedding-3-small", 1536, 8191, 0.02),
            EmbeddingModel("BGE-large-zh-v1.5", 1024, 512, 0.0, True),
            EmbeddingModel("BGE-M3", 1024, 8192, 0.0, True),
            EmbeddingModel("E5-large-v2", 1024, 512, 0.0),
            EmbeddingModel("GTE-large-zh", 1024, 512, 0.0, True),
            EmbeddingModel("Cohere-embed-v3", 1024, 512, 0.10),
        ]

    @staticmethod
    def _simulate_embed(text: str, model: EmbeddingModel) -> list[float]:
        seed = sum(ord(c) for c in text) + sum(ord(c) for c in model.name)
        vec = [(seed * (i + 1) % 997) / 997 for i in range(min(model.dimension, 32))]
        norm = math.sqrt(sum(v ** 2 for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def _cosine_sim(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x ** 2 for x in a))
        nb = math.sqrt(sum(x ** 2 for x in b))
        return dot / (na * nb) if na and nb else 0.0

    def evaluate(self, dataset: EvalDataset) -> list[EvalResult]:
        results = []
        for model in self.models:
            doc_embs = [self._simulate_embed(d, model) for d in dataset.documents]
            hits, rr_sum, total_time = 0, 0.0, 0.0

            for q_idx, query in enumerate(dataset.queries):
                start = time.time()
                q_emb = self._simulate_embed(query, model)
                scores = [(i, self._cosine_sim(q_emb, de)) for i, de in enumerate(doc_embs)]
                scores.sort(key=lambda x: x[1], reverse=True)
                total_time += time.time() - start

                top_ids = [s[0] for s in scores[:10]]
                relevant = set(dataset.relevance.get(q_idx, []))
                if relevant & set(top_ids):
                    hits += 1
                for rank, doc_id in enumerate(top_ids, 1):
                    if doc_id in relevant:
                        rr_sum += 1.0 / rank
                        break

            n = len(dataset.queries) or 1
            results.append(EvalResult(
                model=model.name, domain=dataset.domain,
                hit_rate=round(hits / n, 3),
                mrr=round(rr_sum / n, 3),
                avg_latency_ms=round(total_time / n * 1000, 2),
                cost_per_query=round(model.cost_per_million / 1_000_000 * 500, 6),
            ))
        return results


# ============================================================
# 评测数据集
# ============================================================
def build_datasets() -> list[EvalDataset]:
    return [
        EvalDataset("电商",
                     ["防水蓝牙耳机", "轻薄笔记本推荐", "儿童安全座椅"],
                     ["Sony WF-1000XM5 降噪蓝牙耳机 IP68防水",
                      "MacBook Air M3 轻薄笔记本 1.24kg",
                      "Cybex 儿童安全座椅 ISOFIX接口",
                      "华为MatePad平板电脑"],
                     {0: [0], 1: [1], 2: [2]}),
        EvalDataset("金融",
                     ["股权质押风险", "基金净值计算"],
                     ["股权质押业务风险管理办法第三条",
                      "开放式基金净值计算方法与披露规范",
                      "银行间市场利率走势分析"],
                     {0: [0], 1: [1]}),
        EvalDataset("医疗",
                     ["糖尿病用药方案", "高血压治疗指南"],
                     ["二型糖尿病口服降糖药物选择指南",
                      "高血压分级诊疗与用药规范",
                      "常见感冒症状与家庭护理"],
                     {0: [0], 1: [1]}),
        EvalDataset("法律",
                     ["劳动合同解除赔偿", "知识产权侵权"],
                     ["劳动合同法第四十七条经济补偿标准",
                      "知识产权侵权损害赔偿计算方法",
                      "民事诉讼法管辖权规定"],
                     {0: [0], 1: [1]}),
        EvalDataset("技术",
                     ["Kubernetes HPA配置", "Docker网络模式"],
                     ["Kubernetes HPA水平自动扩缩容配置指南",
                      "Docker四种网络模式详解bridge host none overlay",
                      "Nginx反向代理与负载均衡配置"],
                     {0: [0], 1: [1]}),
    ]


# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 60)
    print("Embedding模型评测演示")
    print("=" * 60)

    benchmark = EmbeddingBenchmark()
    datasets = build_datasets()

    # 逐领域评测
    all_results: dict[str, list[EvalResult]] = {}
    for ds in datasets:
        results = benchmark.evaluate(ds)
        all_results[ds.domain] = results

    # 打印各领域 Hit Rate
    print("\n--- Hit Rate@10 对比 ---")
    domains = [ds.domain for ds in datasets]
    header = f"{'模型':<28}" + "".join(f"{d:<8}" for d in domains)
    print(header)
    print("-" * len(header))

    model_names = [m.name for m in benchmark.models]
    for model_name in model_names:
        row = f"{model_name:<28}"
        for domain in domains:
            hr = next(r.hit_rate for r in all_results[domain] if r.model == model_name)
            row += f"{hr:<8.1%}"
        print(row)

    # 成本对比
    print("\n--- 成本对比 ---")
    print(f"{'模型':<28} {'维度':<8} {'$/百万Token':<14} {'中文原生'}")
    print("-" * 60)
    for m in benchmark.models:
        cn = "✅" if m.chinese_native else "❌"
        cost = f"${m.cost_per_million}" if m.cost_per_million > 0 else "免费(自部署)"
        print(f"{m.name:<28} {m.dimension:<8} {cost:<14} {cn}")

    # 选型建议
    print("\n" + "=" * 60)
    print("选型建议")
    print("=" * 60)
    tips = [
        ("中文场景首选", "BGE-M3", "多语言+长文本+综合表现最佳"),
        ("英文场景首选", "text-embedding-3-small", "性价比高"),
        ("预算充足", "text-embedding-3-large", "高维度高精度"),
        ("完全自部署", "BGE-large-zh-v1.5", "零API成本"),
    ]
    for scene, model, reason in tips:
        print(f"  {scene:<16} → {model:<28} {reason}")


if __name__ == "__main__":
    main()
