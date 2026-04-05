"""
语义缓存演示
对应文章：49-语义缓存当重复请求命中相同Prompt时
"""
from __future__ import annotations
import time
import math
import random
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """缓存条目"""
    query: str
    embedding: list[float]
    response: str
    created_at: float
    ttl_seconds: int = 3600
    hit_count: int = 0
    tenant_id: str = "default"

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl_seconds


class SemanticCache:
    """语义缓存引擎"""

    def __init__(self, similarity_threshold: float = 0.92,
                 default_ttl: int = 3600, max_entries: int = 10000):
        self.threshold = similarity_threshold
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self.entries: list[CacheEntry] = []
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, query_embedding, tenant_id="default"):
        best_score = 0.0
        best_entry = None

        for entry in self.entries:
            if entry.is_expired or entry.tenant_id != tenant_id:
                continue
            score = self._cosine_similarity(query_embedding, entry.embedding)
            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry and best_score >= self.threshold:
            best_entry.hit_count += 1
            self.stats["hits"] += 1
            return best_entry.response

        self.stats["misses"] += 1
        return None

    def put(self, query: str, embedding: list[float], response: str,
            tenant_id: str = "default", ttl: int | None = None):
        if len(self.entries) >= self.max_entries:
            self._evict()
        entry = CacheEntry(
            query=query,
            embedding=embedding,
            response=response,
            created_at=time.time(),
            ttl_seconds=ttl or self.default_ttl,
            tenant_id=tenant_id,
        )
        self.entries.append(entry)

    def _evict(self):
        self.entries = [e for e in self.entries if not e.is_expired]
        if len(self.entries) >= self.max_entries:
            self.entries.sort(key=lambda e: e.hit_count)
            removed = len(self.entries) - int(self.max_entries * 0.8)
            self.entries = self.entries[removed:]
            self.stats["evictions"] += removed

    def invalidate_by_tenant(self, tenant_id: str) -> int:
        """按租户失效缓存"""
        before = len(self.entries)
        self.entries = [
            e for e in self.entries if e.tenant_id != tenant_id
        ]
        return before - len(self.entries)

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def get_stats(self) -> dict:
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        return {
            **self.stats,
            "total": total,
            "hit_rate": round(hit_rate, 3),
            "cache_size": len(self.entries),
        }


def fake_embedding(text: str, dim: int = 8) -> list[float]:
    """模拟Embedding（演示用，生产中用真实模型）"""
    random.seed(hash(text) % 2**32)
    base = [random.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in base))
    return [x / norm for x in base]


def similar_embedding(base: list[float], noise: float = 0.05) -> list[float]:
    """生成与base相似的embedding"""
    noisy = [x + random.gauss(0, noise) for x in base]
    norm = math.sqrt(sum(x * x for x in noisy))
    return [x / norm for x in noisy]


if __name__ == "__main__":
    cache = SemanticCache(similarity_threshold=0.92, default_ttl=3600)

    # 预热缓存
    faq_items = [
        ("怎么退货", "退货流程：1.申请退货 2.审核 3.寄回 4.退款"),
        ("如何修改地址", "在订单详情页点击修改地址按钮即可"),
        ("支付方式有哪些", "支持微信、支付宝、银行卡等支付方式"),
        ("物流多久到", "一般3-5个工作日送达，偏远地区5-7天"),
    ]

    print("=== 缓存预热 ===")
    for query, response in faq_items:
        emb = fake_embedding(query)
        cache.put(query, emb, response)
        print(f"  已缓存: {query}")

    # 模拟请求
    print("\n=== 模拟请求 ===")
    test_queries = [
        ("退货流程是什么", "怎么退货"),      # 语义相似
        ("我想退货怎么操作", "怎么退货"),    # 语义相似
        ("怎么退货", "怎么退货"),            # 完全相同
        ("如何申请发票", None),              # 新问题
        ("修改收货地址", "如何修改地址"),    # 语义相似
    ]

    for query, expected_match in test_queries:
        emb = fake_embedding(query)
        if expected_match:
            # 生成与预期匹配项相似的embedding
            base_emb = fake_embedding(expected_match)
            emb = similar_embedding(base_emb, noise=0.03)

        result = cache.get(emb)
        status = "命中" if result else "未命中"
        print(f"  [{status}] {query}")
        if result:
            print(f"         -> {result[:40]}...")
        else:
            # 未命中则调用LLM并缓存
            response = f"LLM回答: 关于{query}的详细说明..."
            cache.put(query, emb, response)

    # 统计
    print(f"\n=== 缓存统计 ===")
    stats = cache.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # 多租户隔离演示
    print(f"\n=== 多租户隔离 ===")
    cache.put("退货政策", fake_embedding("退货政策A"),
              "A公司: 7天无理由退货", tenant_id="tenant_a")
    cache.put("退货政策", fake_embedding("退货政策B"),
              "B公司: 15天无理由退货", tenant_id="tenant_b")

    removed = cache.invalidate_by_tenant("tenant_a")
    print(f"  清除tenant_a缓存: {removed}条")
