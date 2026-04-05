"""
RAG落地十大坑演示：分块分析、上下文污染检测、MMR多样性检索
"""

import re
from dataclasses import dataclass


# ============================================================
# 坑1: 分块粒度分析
# ============================================================
class ChunkSizeAnalyzer:
    """分析不同分块大小对检索效果的影响"""

    def split(self, text: str, size: int) -> list[str]:
        words = text.split("。")
        chunks, current = [], ""
        for sentence in words:
            if len(current) + len(sentence) > size:
                if current:
                    chunks.append(current.strip())
                current = sentence
            else:
                current += "。" + sentence if current else sentence
        if current:
            chunks.append(current.strip())
        return chunks

    def analyze(self, document: str, query: str, sizes: list[int]) -> dict:
        results = {}
        for size in sizes:
            chunks = self.split(document, size)
            scores = [self._similarity(query, c) for c in chunks]
            best = max(scores) if scores else 0
            results[size] = {
                "chunk_count": len(chunks),
                "best_score": round(best, 3),
                "avg_len": round(sum(len(c) for c in chunks) / max(len(chunks), 1)),
            }
        return results

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        sa, sb = set(a), set(b)
        return len(sa & sb) / max(len(sa | sb), 1)


# ============================================================
# 坑6: 上下文污染检测
# ============================================================
class ContextPollutionDetector:
    """检测检索结果中的上下文污染"""

    def detect(self, query: str, chunks: list[str], threshold: float = 0.15) -> dict:
        relevant, polluted = [], []
        for chunk in chunks:
            score = self._relevance(query, chunk)
            (relevant if score >= threshold else polluted).append(
                {"chunk": chunk[:60], "score": round(score, 3)}
            )
        total = len(chunks)
        return {
            "relevant": len(relevant),
            "polluted": len(polluted),
            "pollution_rate": f"{len(polluted) / total * 100:.0f}%" if total else "0%",
            "details": {"relevant": relevant, "polluted": polluted},
        }

    @staticmethod
    def _relevance(query: str, chunk: str) -> float:
        q_chars = set(query)
        c_chars = set(chunk)
        return len(q_chars & c_chars) / max(len(q_chars), 1)


# ============================================================
# 坑5: MMR多样性检索
# ============================================================
class MMRRetriever:
    """MMR (Maximal Marginal Relevance) 多样性检索"""

    def __init__(self, documents: list[str]):
        self.documents = documents

    def search(self, query: str, top_k: int = 5, lambda_: float = 0.7) -> list[dict]:
        scored = [(doc, self._sim(query, doc)) for doc in self.documents]
        scored.sort(key=lambda x: x[1], reverse=True)
        candidates = scored[:top_k * 3]

        selected: list[tuple[str, float]] = []
        for _ in range(min(top_k, len(candidates))):
            best_doc, best_score = None, -1
            for doc, rel in candidates:
                if any(doc == s[0] for s in selected):
                    continue
                redundancy = max(
                    (self._sim(doc, s[0]) for s in selected), default=0
                )
                mmr = lambda_ * rel - (1 - lambda_) * redundancy
                if mmr > best_score:
                    best_doc, best_score = doc, mmr
            if best_doc:
                selected.append((best_doc, best_score))

        return [{"doc": d[:60], "score": round(s, 3)} for d, s in selected]

    @staticmethod
    def _sim(a: str, b: str) -> float:
        sa, sb = set(a), set(b)
        return len(sa & sb) / max(len(sa | sb), 1)


# ============================================================
# RAG诊断工具
# ============================================================
class RAGDiagnostics:
    """RAG全链路诊断"""

    def diagnose(self, config: dict) -> list[dict]:
        issues = []
        if config.get("chunk_size", 0) > 1000:
            issues.append({"level": "warning", "component": "chunking",
                          "issue": "分块过大，可能导致检索不精确"})
        if config.get("chunk_size", 0) < 100:
            issues.append({"level": "warning", "component": "chunking",
                          "issue": "分块过小，可能丢失上下文"})
        if not config.get("hybrid_search", False):
            issues.append({"level": "info", "component": "retrieval",
                          "issue": "建议启用混合检索提升召回率"})
        if not config.get("rerank", False):
            issues.append({"level": "info", "component": "retrieval",
                          "issue": "建议启用Rerank提升精度"})
        if config.get("top_k", 0) > 10:
            issues.append({"level": "warning", "component": "context",
                          "issue": "Top-K过大，可能导致上下文污染"})
        if not config.get("evaluation", False):
            issues.append({"level": "critical", "component": "evaluation",
                          "issue": "缺少评估体系，无法量化效果"})
        return issues


# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 60)
    print("RAG落地十大坑演示")
    print("=" * 60)

    # --- 分块粒度分析 ---
    print("\n--- 坑1: 分块粒度分析 ---")
    doc = (
        "退货流程分为三步。第一步，用户在订单页面点击申请退货。"
        "第二步，填写退货原因并上传商品照片。"
        "第三步，将商品寄回指定地址，我们收到后3个工作日内退款。"
        "退货运费由卖家承担。如果商品有质量问题，可以申请全额退款。"
        "会员用户享受优先处理，普通用户按提交顺序处理。"
    )
    analyzer = ChunkSizeAnalyzer()
    results = analyzer.analyze(doc, "退货流程怎么走", [50, 100, 200])
    for size, info in results.items():
        print(f"  分块大小={size}: {info['chunk_count']}块, "
              f"最佳匹配={info['best_score']}, 平均长度={info['avg_len']}")

    # --- 上下文污染检测 ---
    print("\n--- 坑6: 上下文污染检测 ---")
    detector = ContextPollutionDetector()
    chunks = [
        "退货流程分为三步，用户在订单页面点击申请退货",
        "我们的物流合作伙伴包括顺丰、中通、圆通",
        "退货运费由卖家承担，质量问题可全额退款",
        "公司成立于2015年，总部位于上海",
        "会员用户享受优先处理退货服务",
    ]
    result = detector.detect("退货流程怎么走", chunks)
    print(f"  相关: {result['relevant']}条, 污染: {result['polluted']}条, "
          f"污染率: {result['pollution_rate']}")

    # --- MMR多样性检索 ---
    print("\n--- 坑5: MMR多样性检索 ---")
    docs = [
        "退货流程第一步：在订单页面点击申请退货按钮",
        "退货流程第二步：填写退货原因并上传照片",
        "退货流程第三步：将商品寄回指定地址",
        "退货运费政策：卖家承担运费",
        "会员退货优先处理政策说明",
        "物流合作伙伴介绍",
        "售后服务时间：工作日9-18点",
    ]
    retriever = MMRRetriever(docs)
    mmr_results = retriever.search("退货流程", top_k=3)
    print("  MMR检索结果（多样性）:")
    for r in mmr_results:
        print(f"    {r['score']:.3f} | {r['doc']}")

    # --- RAG诊断 ---
    print("\n--- RAG全链路诊断 ---")
    diag = RAGDiagnostics()
    issues = diag.diagnose({
        "chunk_size": 1500, "top_k": 15,
        "hybrid_search": False, "rerank": False, "evaluation": False,
    })
    for issue in issues:
        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[issue["level"]]
        print(f"  {icon} [{issue['component']}] {issue['issue']}")


if __name__ == "__main__":
    main()
