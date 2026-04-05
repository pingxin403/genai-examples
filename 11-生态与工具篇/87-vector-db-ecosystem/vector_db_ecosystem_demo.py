"""
向量数据库生态演示：14款主流方案的核心模式对比
演示Chroma风格、PGVector风格、Qdrant风格、Milvus风格的向量存储
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import math


# ============================================================
# 统一接口抽象
# ============================================================
@dataclass
class Document:
    id: str
    text: str
    embedding: list[float]
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    document: Document
    score: float


class VectorStore(ABC):
    @abstractmethod
    def insert(self, docs: list[Document]) -> int: ...

    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]: ...

    @abstractmethod
    def delete(self, doc_ids: list[str]) -> int: ...


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x ** 2 for x in a))
    nb = math.sqrt(sum(x ** 2 for x in b))
    return dot / (na * nb) if na and nb else 0.0


def simple_embed(text: str, dim: int = 8) -> list[float]:
    """简易文本向量化"""
    values = [0.0] * dim
    for i, ch in enumerate(text):
        values[i % dim] += ord(ch) / 1000
    norm = math.sqrt(sum(v ** 2 for v in values)) or 1.0
    return [v / norm for v in values]


# ============================================================
# Chroma风格：轻量嵌入式
# ============================================================
class ChromaStyleStore(VectorStore):
    def __init__(self):
        self.docs: dict[str, Document] = {}

    def insert(self, docs: list[Document]) -> int:
        for doc in docs:
            self.docs[doc.id] = doc
        return len(docs)

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        results = []
        for doc in self.docs.values():
            score = cosine_similarity(query_embedding, doc.embedding)
            results.append(SearchResult(document=doc, score=score))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def delete(self, doc_ids: list[str]) -> int:
        count = 0
        for did in doc_ids:
            if did in self.docs:
                del self.docs[did]
                count += 1
        return count


# ============================================================
# PGVector风格：SQL + 向量
# ============================================================
class PGVectorStyleStore(VectorStore):
    def __init__(self):
        self.table: list[dict] = []

    def insert(self, docs: list[Document]) -> int:
        for doc in docs:
            self.table.append({
                "id": doc.id, "text": doc.text,
                "embedding": doc.embedding, "metadata": doc.metadata,
            })
        return len(docs)

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        results = []
        for row in self.table:
            dist = sum((a - b) ** 2 for a, b in zip(query_embedding, row["embedding"]))
            doc = Document(id=row["id"], text=row["text"],
                           embedding=row["embedding"], metadata=row["metadata"])
            results.append(SearchResult(document=doc, score=1 / (1 + dist)))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def delete(self, doc_ids: list[str]) -> int:
        before = len(self.table)
        id_set = set(doc_ids)
        self.table = [r for r in self.table if r["id"] not in id_set]
        return before - len(self.table)


# ============================================================
# Qdrant风格：带过滤的向量检索
# ============================================================
class QdrantStyleStore(VectorStore):
    def __init__(self):
        self.points: dict[str, dict] = {}

    def insert(self, docs: list[Document]) -> int:
        for doc in docs:
            self.points[doc.id] = {
                "vector": doc.embedding,
                "payload": {"text": doc.text, **doc.metadata},
            }
        return len(docs)

    def search(self, query_embedding: list[float], top_k: int,
               filter_field: str = None, filter_value=None) -> list[SearchResult]:
        results = []
        for pid, point in self.points.items():
            if filter_field and point["payload"].get(filter_field) != filter_value:
                continue
            score = cosine_similarity(query_embedding, point["vector"])
            doc = Document(id=pid, text=point["payload"]["text"],
                           embedding=point["vector"],
                           metadata={k: v for k, v in point["payload"].items() if k != "text"})
            results.append(SearchResult(document=doc, score=score))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def delete(self, doc_ids: list[str]) -> int:
        count = 0
        for did in doc_ids:
            if did in self.points:
                del self.points[did]
                count += 1
        return count


# ============================================================
# 演示
# ============================================================
def main():
    print("=" * 60)
    print("向量数据库生态演示")
    print("=" * 60)

    # 准备测试文档
    raw_docs = [
        ("doc1", "RAG是检索增强生成的缩写", {"category": "ai"}),
        ("doc2", "PostgreSQL是一款开源关系数据库", {"category": "db"}),
        ("doc3", "向量检索用于语义搜索场景", {"category": "ai"}),
        ("doc4", "Redis支持多种数据结构", {"category": "db"}),
        ("doc5", "Milvus是专用向量数据库", {"category": "db"}),
    ]
    documents = [
        Document(id=rid, text=text, embedding=simple_embed(text), metadata=meta)
        for rid, text, meta in raw_docs
    ]
    query = "向量数据库怎么选"
    query_emb = simple_embed(query)

    # --- Chroma风格 ---
    print("\n--- Chroma风格（轻量嵌入式） ---")
    chroma = ChromaStyleStore()
    chroma.insert(documents)
    for r in chroma.search(query_emb, top_k=3):
        print(f"  [{r.score:.4f}] {r.document.text}")

    # --- PGVector风格 ---
    print("\n--- PGVector风格（SQL+向量） ---")
    pg = PGVectorStyleStore()
    pg.insert(documents)
    for r in pg.search(query_emb, top_k=3):
        print(f"  [{r.score:.4f}] {r.document.text}")

    # --- Qdrant风格（带过滤） ---
    print("\n--- Qdrant风格（带过滤检索） ---")
    qdrant = QdrantStyleStore()
    qdrant.insert(documents)
    print("  全量检索:")
    for r in qdrant.search(query_emb, top_k=3):
        print(f"    [{r.score:.4f}] {r.document.text}")
    print("  过滤 category=db:")
    for r in qdrant.search(query_emb, top_k=3, filter_field="category", filter_value="db"):
        print(f"    [{r.score:.4f}] {r.document.text}")

    # 删除演示
    print("\n--- 删除操作 ---")
    deleted = chroma.delete(["doc1"])
    print(f"  Chroma删除{deleted}条，剩余{len(chroma.docs)}条")

    # 对比总结
    print("\n" + "=" * 60)
    print("向量数据库选型总结")
    print("=" * 60)
    rows = [
        ("Chroma", "嵌入式", "<10万", "零", "原型开发"),
        ("PGVector", "PG扩展", "<100万", "低", "已有PG团队"),
        ("Qdrant", "专用向量库", "百万级", "中", "带过滤检索"),
        ("Milvus", "分布式向量库", "千万级", "高", "大规模生产"),
    ]
    print(f"{'方案':<12} {'类型':<12} {'数据规模':<12} {'运维':<8} {'适用场景'}")
    print("-" * 60)
    for name, typ, scale, ops, scene in rows:
        print(f"{name:<12} {typ:<12} {scale:<12} {ops:<8} {scene}")


if __name__ == "__main__":
    main()
