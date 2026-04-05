"""
知识库即服务演示：多租户RAG平台
对应文章：71-知识库即服务为10个业务线提供统一RAG能力
"""
from __future__ import annotations

import time
import hashlib
import math
from dataclasses import dataclass, field
from enum import Enum


class TenantTier(Enum):
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"


@dataclass
class Tenant:
    tenant_id: str
    name: str
    tier: TenantTier = TenantTier.STANDARD
    max_documents: int = 10000
    max_queries_per_day: int = 5000
    current_docs: int = 0
    daily_queries: int = 0


@dataclass
class Document:
    doc_id: str
    tenant_id: str
    title: str
    content: str
    chunks: list[dict] = field(default_factory=list)
    status: str = "pending"


class RAGPlatform:
    def __init__(self):
        self.tenants: dict[str, Tenant] = {}
        self.documents: dict[str, list[Document]] = {}
        self.vectors: dict[str, list[dict]] = {}

    def register_tenant(self, tid, name, tier=TenantTier.STANDARD) -> Tenant:
        limits = {
            TenantTier.FREE: (1000, 500),
            TenantTier.STANDARD: (10000, 5000),
            TenantTier.PREMIUM: (100000, 50000),
        }
        max_docs, max_q = limits[tier]
        t = Tenant(tid, name, tier, max_docs, max_q)
        self.tenants[tid] = t
        self.documents[tid] = []
        self.vectors[tid] = []
        return t

    def ingest(self, tid: str, title: str, content: str) -> dict:
        t = self.tenants.get(tid)
        if not t:
            return {"error": "tenant_not_found"}
        if t.current_docs >= t.max_documents:
            return {"error": "doc_limit_exceeded"}

        doc_id = hashlib.md5(f"{tid}{title}{time.time()}".encode()).hexdigest()[:12]
        chunks = self._chunk(content)
        vectors = []
        for i, ck in enumerate(chunks):
            vec = self._embed(ck["text"])
            vectors.append({
                "doc_id": doc_id, "chunk_id": f"{doc_id}_c{i}",
                "text": ck["text"], "vector": vec,
                "metadata": {"title": title, "index": i},
            })

        doc = Document(doc_id, tid, title, content, chunks, "completed")
        self.documents[tid].append(doc)
        self.vectors[tid].extend(vectors)
        t.current_docs += 1
        return {"doc_id": doc_id, "chunks": len(chunks), "vectors": len(vectors)}

    def search(self, tid: str, query: str, top_k: int = 5):
        t = self.tenants.get(tid)
        if not t:
            return {"error": "tenant_not_found"}
        if t.daily_queries >= t.max_queries_per_day:
            return {"error": "query_limit_exceeded"}
        t.daily_queries += 1

        qvec = self._embed(query)
        scored = []
        for v in self.vectors.get(tid, []):
            s = self._cosine(qvec, v["vector"])
            bonus = sum(0.05 for w in query.split() if w in v["text"])
            scored.append({**v, "score": round(s + bonus, 4)})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return [{"chunk_id": r["chunk_id"], "text": r["text"][:150],
                 "score": r["score"], "title": r["metadata"]["title"]}
                for r in scored[:top_k]]

    def get_stats(self, tid: str) -> dict:
        t = self.tenants.get(tid)
        if not t:
            return {"error": "tenant_not_found"}
        return {
            "tenant": t.name, "tier": t.tier.value,
            "docs": f"{t.current_docs}/{t.max_documents}",
            "queries": f"{t.daily_queries}/{t.max_queries_per_day}",
            "vectors": len(self.vectors.get(tid, [])),
        }

    def _chunk(self, content, size=100):
        words = content.split()
        chunks = []
        for i in range(0, len(words), size):
            chunks.append({"text": " ".join(words[i:i + size])})
        return chunks or [{"text": content}]

    def _embed(self, text):
        h = hashlib.md5(text.encode()).hexdigest()
        return [int(h[i:i + 2], 16) / 255.0 for i in range(0, 32, 2)]

    def _cosine(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0


def main():
    platform = RAGPlatform()

    print("=" * 60)
    print("知识库即服务(RAG-as-a-Service)演示")
    print("=" * 60)

    # 1. 注册租户
    print("\n--- 1. 注册租户 ---")
    tenants = [
        ("cs", "客服系统", TenantTier.PREMIUM),
        ("sales", "销售助手", TenantTier.STANDARD),
        ("hr", "HR知识库", TenantTier.FREE),
    ]
    for tid, name, tier in tenants:
        t = platform.register_tenant(tid, name, tier)
        print(f"  [{tid}] {name} tier={tier.value} "
              f"doc_limit={t.max_documents} query_limit={t.max_queries_per_day}")

    # 2. 摄入文档
    print("\n--- 2. 摄入文档 ---")
    docs = [
        ("cs", "退货政策", "用户可以在收到商品后7天内申请退货 需要保持商品完好 退货运费由买家承担 退款将在收到退货后3个工作日内处理"),
        ("cs", "配送说明", "标准配送3到5个工作日 加急配送1到2个工作日 偏远地区可能延迟 支持顺丰和中通快递"),
        ("sales", "产品手册", "我们的AI助手支持多轮对话 知识库检索 工具调用等功能 适用于客服 销售 内部问答等场景"),
        ("hr", "请假制度", "年假15天 病假需要医院证明 事假需要提前3天申请 婚假10天 产假按国家规定执行"),
    ]
    for tid, title, content in docs:
        result = platform.ingest(tid, title, content)
        if isinstance(result, dict) and "doc_id" in result:
            print(f"  [{tid}] {title}: chunks={result['chunks']} vectors={result['vectors']}")

    # 3. 租户隔离检索
    print("\n--- 3. 租户隔离检索 ---")
    queries = [
        ("cs", "退货流程是什么"),
        ("sales", "产品有什么功能"),
        ("hr", "怎么请假"),
    ]
    for tid, query in queries:
        results = platform.search(tid, query, top_k=2)
        print(f"\n  [{tid}] 查询: {query}")
        if isinstance(results, list):
            for r in results:
                print(f"    -> [{r['title']}] score={r['score']} text={r['text'][:60]}...")
        else:
            print(f"    -> 错误: {results}")

    # 4. 跨租户隔离验证
    print("\n--- 4. 跨租户隔离验证 ---")
    results = platform.search("hr", "退货流程")
    print(f"  HR租户搜索'退货流程': {len(results) if isinstance(results, list) else 0}条结果")
    if isinstance(results, list):
        for r in results:
            print(f"    -> [{r['title']}] (应该只有HR的文档)")

    # 5. 租户统计
    print("\n--- 5. 租户统计 ---")
    for tid in ["cs", "sales", "hr"]:
        stats = platform.get_stats(tid)
        print(f"  [{tid}] docs={stats['docs']} queries={stats['queries']} "
              f"vectors={stats['vectors']} tier={stats['tier']}")


if __name__ == "__main__":
    main()
