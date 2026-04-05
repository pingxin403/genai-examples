"""
多租户向量隔离演示：集合级 / 分区级 / 标签过滤
对应文章：65-多租户隔离不同客户的知识在向量库怎么隔离
"""

import time
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class VectorRecord:
    record_id: str
    tenant_id: str
    content: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    record_id: str
    content: str
    score: float
    tenant_id: str


def cosine_sim(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x ** 2 for x in a) ** 0.5
    norm_b = sum(x ** 2 for x in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


class TenantIsolationStrategy(ABC):
    @abstractmethod
    def insert(self, record: VectorRecord): ...
    @abstractmethod
    def search(self, tenant_id: str, query_embedding: list[float], top_k: int) -> list[SearchResult]: ...
    @abstractmethod
    def delete_tenant(self, tenant_id: str) -> int: ...
    @abstractmethod
    def get_stats(self) -> dict: ...


class CollectionIsolation(TenantIsolationStrategy):
    def __init__(self):
        self.collections: dict[str, list[VectorRecord]] = {}

    def insert(self, record: VectorRecord):
        self.collections.setdefault(record.tenant_id, []).append(record)

    def search(self, tenant_id: str, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
        records = self.collections.get(tenant_id, [])
        scored = [SearchResult(r.record_id, r.content, cosine_sim(query_embedding, r.embedding), r.tenant_id) for r in records]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def delete_tenant(self, tenant_id: str) -> int:
        return len(self.collections.pop(tenant_id, []))

    def get_stats(self) -> dict:
        return {"strategy": "collection", "tenants": len(self.collections),
                "per_tenant": {t: len(r) for t, r in self.collections.items()}}


class PartitionIsolation(TenantIsolationStrategy):
    def __init__(self):
        self.partitions: dict[str, list[VectorRecord]] = {}

    def insert(self, record: VectorRecord):
        self.partitions.setdefault(record.tenant_id, []).append(record)

    def search(self, tenant_id: str, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
        records = self.partitions.get(tenant_id, [])
        scored = [SearchResult(r.record_id, r.content, cosine_sim(query_embedding, r.embedding), r.tenant_id) for r in records]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def delete_tenant(self, tenant_id: str) -> int:
        return len(self.partitions.pop(tenant_id, []))

    def get_stats(self) -> dict:
        return {"strategy": "partition", "tenants": len(self.partitions),
                "total": sum(len(r) for r in self.partitions.values())}


class MetadataFilterIsolation(TenantIsolationStrategy):
    def __init__(self):
        self.records: list[VectorRecord] = []

    def insert(self, record: VectorRecord):
        self.records.append(record)

    def search(self, tenant_id: str, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
        filtered = [r for r in self.records if r.tenant_id == tenant_id]
        scored = [SearchResult(r.record_id, r.content, cosine_sim(query_embedding, r.embedding), r.tenant_id) for r in filtered]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def delete_tenant(self, tenant_id: str) -> int:
        before = len(self.records)
        self.records = [r for r in self.records if r.tenant_id != tenant_id]
        return before - len(self.records)

    def get_stats(self) -> dict:
        tenants = {}
        for r in self.records:
            tenants[r.tenant_id] = tenants.get(r.tenant_id, 0) + 1
        return {"strategy": "metadata_filter", "total": len(self.records), "per_tenant": tenants}


def main():
    strategies = {
        "集合级隔离": CollectionIsolation(),
        "分区级隔离": PartitionIsolation(),
        "标签过滤": MetadataFilterIsolation(),
    }

    # 准备测试数据
    test_data = [
        VectorRecord("r1", "tenant_A", "A公司退货政策：7天无理由", [1.0, 0.5, 0.0]),
        VectorRecord("r2", "tenant_A", "A公司定价：基础版99元", [0.8, 0.6, 0.1]),
        VectorRecord("r3", "tenant_B", "B公司产品手册：使用指南", [0.9, 0.4, 0.2]),
        VectorRecord("r4", "tenant_B", "B公司内部流程：审批规范", [0.7, 0.3, 0.5]),
        VectorRecord("r5", "tenant_C", "C公司技术文档：API接口", [0.6, 0.8, 0.3]),
    ]

    query_embedding = [0.9, 0.5, 0.1]

    print("=" * 60)
    print("多租户向量隔离演示")
    print("=" * 60)

    for name, strategy in strategies.items():
        print(f"\n{'='*40}")
        print(f"策略: {name}")
        print(f"{'='*40}")

        # 插入数据
        for record in test_data:
            strategy.insert(record)

        # 租户A检索
        results_a = strategy.search("tenant_A", query_embedding, top_k=3)
        print(f"\n  tenant_A 检索结果 ({len(results_a)} 条):")
        for r in results_a:
            print(f"    [{r.tenant_id}] {r.content} (score={r.score:.3f})")

        # 租户B检索
        results_b = strategy.search("tenant_B", query_embedding, top_k=3)
        print(f"\n  tenant_B 检索结果 ({len(results_b)} 条):")
        for r in results_b:
            print(f"    [{r.tenant_id}] {r.content} (score={r.score:.3f})")

        # 验证隔离
        a_leak = any(r.tenant_id != "tenant_A" for r in results_a)
        b_leak = any(r.tenant_id != "tenant_B" for r in results_b)
        print(f"\n  隔离验证: A泄露={'❌' if a_leak else '✅'} B泄露={'❌' if b_leak else '✅'}")

        # 删除租户
        deleted = strategy.delete_tenant("tenant_C")
        print(f"  删除tenant_C: {deleted}条记录")

        print(f"  统计: {strategy.get_stats()}")


if __name__ == "__main__":
    main()
