"""
RAG进化史：从Naive到Modular的三代架构演示
配套文章：《RAG进化史：从Naive到Modular，你的架构在第几层？》

本示例使用模拟数据演示三代RAG架构的核心差异，无需外部API。
"""

import time
import random
import numpy as np
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum


# ============================================================
# 基础组件：模拟向量库、LLM、Reranker
# ============================================================

@dataclass
class Document:
    """文档块"""
    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class MockVectorStore:
    """模拟向量库：基于关键词重叠计算相似度"""

    def __init__(self):
        self.documents: list[Document] = []

    def add(self, texts: list[str], metadata_list: list[dict] = None):
        for i, text in enumerate(texts):
            meta = metadata_list[i] if metadata_list else {}
            self.documents.append(
                Document(id=f"doc_{len(self.documents)}", content=text, metadata=meta)
            )

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """基于词重叠的模拟向量检索"""
        query_words = set(query.lower().replace("？", "").replace("？", "").split())
        scored = []
        for doc in self.documents:
            doc_words = set(doc.content.lower().split())
            overlap = len(query_words & doc_words)
            score = overlap / max(len(query_words), 1)
            noise = random.uniform(-0.1, 0.1)
            scored.append(Document(
                id=doc.id, content=doc.content,
                metadata=doc.metadata, score=score + noise
            ))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]


class MockKeywordStore:
    """模拟BM25关键词检索"""

    def __init__(self):
        self.documents: list[Document] = []

    def add(self, texts: list[str]):
        for text in texts:
            self.documents.append(
                Document(id=f"kw_{len(self.documents)}", content=text)
            )

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        query_chars = set(query)
        scored = []
        for doc in self.documents:
            doc_chars = set(doc.content)
            overlap = len(query_chars & doc_chars)
            score = overlap / max(len(query_chars), 1)
            scored.append(Document(
                id=doc.id, content=doc.content, score=score
            ))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]


class MockReranker:
    """模拟Rerank精排器"""

    def rank(self, query: str, documents: list[Document]) -> list[Document]:
        for doc in documents:
            relevance = 0.0
            query_lower = query.lower()
            content_lower = doc.content.lower()
            # 简单的关键词匹配打分
            for word in query_lower.split():
                if word in content_lower:
                    relevance += 0.2
            doc.score = min(relevance + random.uniform(0, 0.3), 1.0)
        return sorted(documents, key=lambda x: x.score, reverse=True)


class MockLLM:
    """模拟LLM：基于上下文关键词生成回答"""

    def generate(self, prompt: str) -> str:
        if "改写" in prompt or "rewrite" in prompt.lower():
            return "退货流程\n如何申请退货退款\n退货政策和步骤"
        if "判断" in prompt and "类型" in prompt:
            return "1"
        if "分解" in prompt:
            return "退货需要什么条件？\n退货的具体步骤是什么？"
        if "评估" in prompt and "质量" in prompt:
            return str(round(random.uniform(0.6, 0.95), 2))
        if "资料" in prompt:
            return "[基于检索结果生成] 退货流程：登录账户→提交退货申请→等待审核→寄回商品→确认退款。"
        return "这是一个模拟的LLM回答。"


# ============================================================
# 示例知识库数据
# ============================================================

KNOWLEDGE_BASE = [
    "退货流程 第一步 登录账户 进入订单管理 找到需要退货的订单",
    "退货流程 第二步 点击申请退货 填写退货原因 上传商品照片",
    "退货流程 第三步 等待客服审核 通常1-2个工作日内完成审核",
    "退货流程 第四步 审核通过后 按照提供的地址寄回商品 保留快递单号",
    "退货流程 第五步 仓库收到商品并确认无误后 3-5个工作日内退款到原支付账户",
    "退货政策 商品签收后7天内可申请无理由退货 需保持商品完好",
    "退货政策 定制商品 食品 贴身衣物等特殊商品不支持无理由退货",
    "换货流程 如需换货 请先申请退货 收到退款后重新下单购买",
    "产品参数 型号A100 尺寸 120x80x45mm 重量 350g 颜色 黑色 白色 蓝色",
    "竞品分析 与B品牌相比 我们的产品在续航和防水性能上有明显优势",
    "促销活动 双十一期间全场满300减50 部分商品买一送一",
    "会员权益 金卡会员享受免费退换货 优先客服 专属折扣等权益",
]


# ============================================================
# 第一代：朴素RAG
# ============================================================

class NaiveRAG:
    """第一代：朴素RAG"""

    def __init__(self):
        self.vector_store = MockVectorStore()
        self.llm = MockLLM()

    def ingest(self, documents: list[str]):
        """直接灌入向量库，不做预处理"""
        self.vector_store.add(documents)
        print(f"  [Naive] 已导入 {len(documents)} 个文档块")

    def query(self, question: str) -> dict:
        """单次检索 + 直接生成"""
        start = time.time()

        # 1. 向量检索
        results = self.vector_store.search(question, top_k=5)

        # 2. 拼接上下文
        context = "\n".join([f"- {r.content}" for r in results])

        # 3. 生成回答
        prompt = f"根据以下资料回答问题。\n\n资料：\n{context}\n\n问题：{question}"
        answer = self.llm.generate(prompt)

        elapsed = time.time() - start
        return {
            "answer": answer,
            "sources": len(results),
            "latency_ms": round(elapsed * 1000),
            "steps": ["向量检索", "拼接Prompt", "LLM生成"],
        }


# ============================================================
# 第二代：高级RAG
# ============================================================

class AdvancedRAG:
    """第二代：高级RAG"""

    def __init__(self):
        self.vector_store = MockVectorStore()
        self.keyword_store = MockKeywordStore()
        self.reranker = MockReranker()
        self.llm = MockLLM()

    def ingest(self, documents: list[str]):
        self.vector_store.add(documents)
        self.keyword_store.add(documents)
        print(f"  [Advanced] 已导入 {len(documents)} 个文档块（向量+关键词双索引）")

    def rewrite_query(self, question: str) -> list[str]:
        """查询改写"""
        prompt = f"请将以下问题改写为3个不同的检索查询：\n{question}"
        rewritten = self.llm.generate(prompt)
        queries = [q.strip() for q in rewritten.split("\n") if q.strip()]
        return [question] + queries[:3]

    def hybrid_search(self, queries: list[str], top_k: int = 20) -> list[Document]:
        """混合检索"""
        all_results = []
        seen = set()
        for q in queries:
            for r in self.vector_store.search(q, top_k=10):
                if r.id not in seen:
                    all_results.append(r)
                    seen.add(r.id)
            for r in self.keyword_store.search(q, top_k=10):
                key = r.content[:50]
                if key not in seen:
                    all_results.append(r)
                    seen.add(key)
        return all_results[:top_k]

    def query(self, question: str) -> dict:
        start = time.time()

        # 1. 查询改写
        queries = self.rewrite_query(question)

        # 2. 混合检索
        candidates = self.hybrid_search(queries, top_k=15)

        # 3. Rerank精排
        ranked = self.reranker.rank(question, candidates)
        top_docs = ranked[:5]

        # 4. 生成回答
        context = "\n".join([f"- {d.content}" for d in top_docs])
        prompt = f"根据以下资料回答问题。\n\n资料：\n{context}\n\n问题：{question}"
        answer = self.llm.generate(prompt)

        elapsed = time.time() - start
        return {
            "answer": answer,
            "sources": len(top_docs),
            "candidates_before_rerank": len(candidates),
            "latency_ms": round(elapsed * 1000),
            "steps": ["查询改写", "混合检索", "Rerank精排", "LLM生成"],
        }


# ============================================================
# 第三代：模块化RAG
# ============================================================

class QueryIntent(Enum):
    KNOWLEDGE_QA = "knowledge_qa"
    CHITCHAT = "chitchat"
    COMPLEX = "complex"


class RAGModule(ABC):
    @abstractmethod
    def process(self, ctx: dict) -> dict:
        pass


class IntentRouter(RAGModule):
    """意图路由模块"""
    def __init__(self, llm):
        self.llm = llm

    def process(self, ctx: dict) -> dict:
        question = ctx["question"].lower()
        # 简单规则路由（生产环境用LLM分类）
        if any(w in question for w in ["你好", "谢谢", "再见", "哈哈"]):
            ctx["intent"] = QueryIntent.CHITCHAT
        elif len(question) > 30 or "并且" in question or "同时" in question:
            ctx["intent"] = QueryIntent.COMPLEX
        else:
            ctx["intent"] = QueryIntent.KNOWLEDGE_QA
        return ctx


class SimpleRetriever(RAGModule):
    """简单检索模块（快速通道）"""
    def __init__(self, store):
        self.store = store

    def process(self, ctx: dict) -> dict:
        results = self.store.search(ctx["question"], top_k=3)
        ctx["retrieved_docs"] = results
        return ctx


class FullRetriever(RAGModule):
    """完整检索模块（查询改写+混合检索+Rerank）"""
    def __init__(self, vec_store, kw_store, reranker, llm):
        self.vec_store = vec_store
        self.kw_store = kw_store
        self.reranker = reranker
        self.llm = llm

    def process(self, ctx: dict) -> dict:
        question = ctx["question"]
        # 查询改写
        prompt = f"请将以下问题改写为3个检索查询：\n{question}"
        rewritten = self.llm.generate(prompt).split("\n")
        queries = [question] + [q.strip() for q in rewritten if q.strip()][:3]

        # 混合检索
        all_docs = []
        seen = set()
        for q in queries:
            for r in self.vec_store.search(q, top_k=10):
                if r.id not in seen:
                    all_docs.append(r)
                    seen.add(r.id)

        # Rerank
        ranked = self.reranker.rank(question, all_docs)
        ctx["retrieved_docs"] = ranked[:5]
        return ctx


class Generator(RAGModule):
    """生成模块"""
    def __init__(self, llm):
        self.llm = llm

    def process(self, ctx: dict) -> dict:
        docs = ctx.get("retrieved_docs", [])
        question = ctx["question"]
        if docs:
            context = "\n".join([f"- {d.content}" for d in docs])
            prompt = f"根据以下资料回答问题。\n\n资料：\n{context}\n\n问题：{question}"
        else:
            prompt = f"请回答：{question}"
        ctx["answer"] = self.llm.generate(prompt)
        return ctx


class QualityChecker(RAGModule):
    """质量检查模块"""
    def __init__(self, llm, threshold=0.7):
        self.llm = llm
        self.threshold = threshold

    def process(self, ctx: dict) -> dict:
        score = round(random.uniform(0.65, 0.95), 2)
        ctx["quality_score"] = score
        ctx["quality_pass"] = score >= self.threshold
        return ctx


class ModularRAG:
    """第三代：模块化RAG"""

    def __init__(self):
        self.llm = MockLLM()
        self.vec_store = MockVectorStore()
        self.kw_store = MockKeywordStore()
        self.reranker = MockReranker()

        # 初始化模块
        self.router = IntentRouter(self.llm)
        self.simple_retriever = SimpleRetriever(self.vec_store)
        self.full_retriever = FullRetriever(
            self.vec_store, self.kw_store, self.reranker, self.llm
        )
        self.generator = Generator(self.llm)
        self.checker = QualityChecker(self.llm)

        # Pipeline定义
        self.pipelines = {
            QueryIntent.KNOWLEDGE_QA: [self.simple_retriever, self.generator],
            QueryIntent.COMPLEX: [self.full_retriever, self.generator, self.checker],
            QueryIntent.CHITCHAT: [self.generator],
        }

    def ingest(self, documents: list[str]):
        self.vec_store.add(documents)
        self.kw_store.add(documents)
        print(f"  [Modular] 已导入 {len(documents)} 个文档块（模块化索引）")

    def query(self, question: str) -> dict:
        start = time.time()
        ctx = {"question": question}

        # 1. 意图路由
        ctx = self.router.process(ctx)
        intent = ctx["intent"]

        # 2. 执行对应Pipeline
        pipeline = self.pipelines.get(intent, self.pipelines[QueryIntent.KNOWLEDGE_QA])
        steps = ["意图路由"]
        for module in pipeline:
            ctx = module.process(ctx)
            steps.append(module.__class__.__name__)

        elapsed = time.time() - start
        return {
            "answer": ctx.get("answer", "无法回答"),
            "intent": intent.value,
            "quality_score": ctx.get("quality_score"),
            "sources": len(ctx.get("retrieved_docs", [])),
            "latency_ms": round(elapsed * 1000),
            "steps": steps,
        }


# ============================================================
# 主程序：对比三代RAG
# ============================================================

def main():
    print("=" * 70)
    print("🧱 RAG进化史：三代架构对比演示")
    print("=" * 70)

    test_questions = [
        "怎么退东西？",
        "退货政策是什么？有什么限制吗？并且换货怎么操作？",
        "你好",
    ]

    # 初始化三代RAG
    print("\n📦 初始化知识库...")
    naive = NaiveRAG()
    naive.ingest(KNOWLEDGE_BASE)

    advanced = AdvancedRAG()
    advanced.ingest(KNOWLEDGE_BASE)

    modular = ModularRAG()
    modular.ingest(KNOWLEDGE_BASE)

    # 逐个问题对比
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'─' * 70}")
        print(f"❓ 测试问题 {i}: {question}")
        print(f"{'─' * 70}")

        # 朴素RAG
        print(f"\n  🔹 第一代 - 朴素RAG:")
        r1 = naive.query(question)
        print(f"    流程: {' → '.join(r1['steps'])}")
        print(f"    召回: {r1['sources']} 条文档")
        print(f"    延迟: {r1['latency_ms']}ms")
        print(f"    回答: {r1['answer'][:80]}...")

        # 高级RAG
        print(f"\n  🔸 第二代 - 高级RAG:")
        r2 = advanced.query(question)
        print(f"    流程: {' → '.join(r2['steps'])}")
        print(f"    候选: {r2['candidates_before_rerank']} → 精排后 {r2['sources']} 条")
        print(f"    延迟: {r2['latency_ms']}ms")
        print(f"    回答: {r2['answer'][:80]}...")

        # 模块化RAG
        print(f"\n  🔶 第三代 - 模块化RAG:")
        r3 = modular.query(question)
        print(f"    意图: {r3['intent']}")
        print(f"    流程: {' → '.join(r3['steps'])}")
        print(f"    召回: {r3['sources']} 条文档")
        if r3.get("quality_score"):
            print(f"    质量: {r3['quality_score']}")
        print(f"    延迟: {r3['latency_ms']}ms")
        print(f"    回答: {r3['answer'][:80]}...")

    # 总结对比
    print(f"\n{'=' * 70}")
    print("📊 三代RAG架构对比总结")
    print(f"{'=' * 70}")
    print(f"{'指标':<20} {'朴素RAG':<15} {'高级RAG':<15} {'模块化RAG':<15}")
    print(f"{'─' * 65}")
    print(f"{'检索策略':<18} {'单次向量':<13} {'混合+Rerank':<13} {'自适应路由':<13}")
    print(f"{'查询优化':<18} {'无':<13} {'查询改写':<13} {'意图+改写':<13}")
    print(f"{'质量保障':<18} {'无':<13} {'Rerank':<13} {'质量反馈':<13}")
    print(f"{'灵活性':<19} {'低':<13} {'中':<13} {'高':<13}")
    print(f"{'适用场景':<18} {'POC/Demo':<13} {'单领域生产':<13} {'企业级平台':<13}")


if __name__ == "__main__":
    main()
