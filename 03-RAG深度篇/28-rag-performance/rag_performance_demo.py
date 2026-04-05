"""
RAG性能优化演示
配套文章：《RAG性能优化：从2秒到200毫秒的优化之路》

演示内容：
1. 语义缓存
2. 并行检索
3. 热点预计算
4. 索引参数调优
"""

import hashlib
import time
import random
import numpy as np
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout


# ============================================================
# 1. 语义缓存
# ============================================================

class SemanticCache:
    """语义缓存：基于向量相似度的query缓存"""

    def __init__(self, similarity_threshold=0.92, max_size=10000, ttl_seconds=3600):
        self.threshold = similarity_threshold
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache = []
        self.stats = {"hits": 0, "misses": 0}

    def get(self, query_embedding):
        now = time.time()
        for emb, answer, ts in self.cache:
            if now - ts > self.ttl:
                continue
            sim = self._cosine_sim(query_embedding, emb)
            if sim >= self.threshold:
                self.stats["hits"] += 1
                return answer
        self.stats["misses"] += 1
        return None

    def put(self, query_embedding, answer):
        self.cache.append((query_embedding, answer, time.time()))
        if len(self.cache) > self.max_size:
            self.cache = self.cache[-self.max_size:]

    def hit_rate(self):
        total = self.stats["hits"] + self.stats["misses"]
        return self.stats["hits"] / total if total > 0 else 0.0

    def _cosine_sim(self, a, b):
        a, b = np.array(a), np.array(b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / norm) if norm > 0 else 0.0


# ============================================================
# 2. 并行检索
# ============================================================

class ParallelRetriever:
    """并行检索器：向量+BM25同时执行"""

    def __init__(self, vector_fn, bm25_fn):
        self.vector_fn = vector_fn
        self.bm25_fn = bm25_fn

    def search(self, query, top_k=10, timeout=0.5):
        start = time.time()
        with ThreadPoolExecutor(max_workers=2) as executor:
            vec_future = executor.submit(self.vector_fn, query, top_k)
            bm25_future = executor.submit(self.bm25_fn, query, top_k)

            vec_results = vec_future.result(timeout=timeout)
            try:
                bm25_results = bm25_future.result(timeout=timeout)
            except FuturesTimeout:
                bm25_results = []

        merged = self._merge(vec_results, bm25_results, top_k)
        elapsed = (time.time() - start) * 1000
        return {"results": merged, "latency_ms": round(elapsed, 1)}

    def _merge(self, a, b, top_k):
        seen = set()
        merged = []
        for r in a + b:
            key = r.get("id", str(r)[:50])
            if key not in seen:
                seen.add(key)
                merged.append(r)
        return merged[:top_k]


# ============================================================
# 3. 热点预计算
# ============================================================

class HotQuestionPrecomputer:
    """热点问题预计算器"""

    def __init__(self):
        self.precomputed = {}

    def precompute(self, hot_queries, generate_fn):
        for query in hot_queries:
            key = hashlib.md5(query.encode()).hexdigest()
            answer = generate_fn(query)
            self.precomputed[key] = {"answer": answer, "ts": time.time()}
        return len(self.precomputed)

    def try_hit(self, query, ttl=86400):
        key = hashlib.md5(query.encode()).hexdigest()
        entry = self.precomputed.get(key)
        if entry and time.time() - entry["ts"] < ttl:
            return entry["answer"]
        return None


# ============================================================
# 4. 索引参数调优
# ============================================================

class IndexTuner:
    """HNSW索引参数调优器"""

    PRESETS = {
        "low_latency": {"M": 8, "efConstruction": 128, "efSearch": 64},
        "balanced": {"M": 16, "efConstruction": 256, "efSearch": 128},
        "high_recall": {"M": 32, "efConstruction": 512, "efSearch": 256},
    }

    def recommend(self, data_size, latency_budget_ms, recall_target):
        if latency_budget_ms < 20 and data_size < 1_000_000:
            return "low_latency", self.PRESETS["low_latency"]
        elif recall_target > 0.95:
            return "high_recall", self.PRESETS["high_recall"]
        return "balanced", self.PRESETS["balanced"]

    def estimate(self, preset_name, data_size):
        params = self.PRESETS[preset_name]
        base = 5 + data_size / 100000 * 2
        latency = base * (params["M"] / 16) * (params["efSearch"] / 128)
        recall = min(0.99, 0.85 + params["efSearch"] / 1000)
        memory = data_size * params["M"] * 4 / 1024 / 1024
        return {
            "latency_ms": round(latency, 1),
            "recall": round(recall, 4),
            "memory_mb": round(memory, 1),
        }


# ============================================================
# 演示
# ============================================================

def mock_embedding(text):
    np.random.seed(hash(text) % 2**32)
    v = np.random.rand(64).astype(np.float32)
    return (v / np.linalg.norm(v)).tolist()


def mock_vector_search(query, top_k):
    time.sleep(random.uniform(0.05, 0.15))
    return [{"id": f"vec_{i}", "score": round(random.random(), 3)} for i in range(top_k)]


def mock_bm25_search(query, top_k):
    time.sleep(random.uniform(0.03, 0.1))
    return [{"id": f"bm25_{i}", "score": round(random.random(), 3)} for i in range(top_k)]


def mock_generate(query):
    return f"关于'{query}'的预生成回答。"


def main():
    random.seed(42)
    np.random.seed(42)

    print("=" * 60)
    print("⚡ RAG性能优化演示")
    print("=" * 60)

    # --- 1. 语义缓存 ---
    print("\n--- 1. 语义缓存 ---")
    cache = SemanticCache(similarity_threshold=0.92)
    emb1 = mock_embedding("年假天数怎么算")
    cache.put(emb1, "工龄5年以下享有7天年假")

    # 相似query命中
    emb2 = mock_embedding("年假天数怎么算")
    hit = cache.get(emb2)
    print(f"  相同query命中: {hit is not None} → {hit}")

    # 不同query未命中
    emb3 = mock_embedding("报销流程是什么")
    miss = cache.get(emb3)
    print(f"  不同query命中: {miss is not None}")
    print(f"  缓存命中率: {cache.hit_rate():.0%}")

    # --- 2. 并行检索 ---
    print("\n--- 2. 并行检索 ---")
    retriever = ParallelRetriever(mock_vector_search, mock_bm25_search)

    # 串行对比
    start = time.time()
    mock_vector_search("test", 5)
    mock_bm25_search("test", 5)
    serial_ms = (time.time() - start) * 1000

    result = retriever.search("年假天数", top_k=5)
    print(f"  串行延迟: {serial_ms:.0f}ms")
    print(f"  并行延迟: {result['latency_ms']}ms")
    print(f"  合并结果数: {len(result['results'])}")

    # --- 3. 热点预计算 ---
    print("\n--- 3. 热点预计算 ---")
    precomputer = HotQuestionPrecomputer()
    hot_queries = ["年假天数怎么算", "报销流程是什么", "加班费怎么算"]
    count = precomputer.precompute(hot_queries, mock_generate)
    print(f"  预计算了 {count} 个热点问题")

    hit = precomputer.try_hit("年假天数怎么算")
    print(f"  热点命中: {hit}")
    miss = precomputer.try_hit("社保基数怎么定")
    print(f"  非热点: {miss}")

    # --- 4. 索引参数调优 ---
    print("\n--- 4. 索引参数调优 ---")
    tuner = IndexTuner()
    for preset in ["low_latency", "balanced", "high_recall"]:
        perf = tuner.estimate(preset, 1_000_000)
        print(f"  {preset:15s}: 延迟={perf['latency_ms']:>6.1f}ms, "
              f"召回={perf['recall']:.4f}, 内存={perf['memory_mb']:.0f}MB")

    name, params = tuner.recommend(1_000_000, latency_budget_ms=30, recall_target=0.95)
    print(f"  推荐方案: {name} → {params}")

    # --- 综合效果 ---
    print("\n--- 综合效果对比 ---")
    print(f"  {'优化手段':<16} {'优化前':>10} {'优化后':>10} {'降幅':>8}")
    print(f"  {'-'*48}")
    rows = [
        ("语义缓存(命中)", "2000ms", "15ms", "-99%"),
        ("并行检索", "500ms", "280ms", "-44%"),
        ("热点预计算(命中)", "2000ms", "5ms", "-99%"),
        ("HNSW调优", "200ms", "30ms", "-85%"),
        ("综合P95", "3500ms", "600ms", "-83%"),
    ]
    for name, before, after, drop in rows:
        print(f"  {name:<16} {before:>10} {after:>10} {drop:>8}")

    print("\n" + "=" * 60)
    print("✅ 演示完成！")


if __name__ == "__main__":
    main()
