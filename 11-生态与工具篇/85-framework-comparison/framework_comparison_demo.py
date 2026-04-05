"""
AI应用框架对比演示：LangChain vs LlamaIndex vs Haystack
演示三种框架的核心设计模式差异
"""


# ============================================================
# LangChain风格：Chain式编排
# ============================================================
class LangChainStyleRAG:
    """模拟LangChain的Chain式编排"""

    def __init__(self):
        self.documents = []
        self.embeddings = {}

    def load_documents(self, docs: list[str]):
        self.documents = docs
        for i, doc in enumerate(docs):
            self.embeddings[i] = self._embed(doc)

    def _embed(self, text: str) -> list[float]:
        return [ord(c) / 1000 for c in text[:10]]

    def chain(self, query: str) -> str:
        results = self._retrieve(query, top_k=3)
        context = "\n".join(results)
        prompt = f"基于以下上下文回答问题：\n{context}\n\n问题：{query}"
        return f"[LangChain] 基于{len(results)}个文档生成回答"

    def _retrieve(self, query: str, top_k: int) -> list[str]:
        query_emb = self._embed(query)
        scored = []
        for i, doc in enumerate(self.documents):
            score = sum(a * b for a, b in zip(query_emb, self.embeddings[i]))
            scored.append((doc, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:top_k]]


# ============================================================
# LlamaIndex风格：Index优先
# ============================================================
class LlamaIndexStyleRAG:
    """模拟LlamaIndex的Index优先设计"""

    def __init__(self):
        self.index = {}
        self.nodes = []

    def build_index(self, docs: list[str]):
        for i, doc in enumerate(docs):
            node = {"id": i, "text": doc, "embedding": self._embed(doc)}
            self.nodes.append(node)
            for word in doc:
                self.index.setdefault(word, []).append(i)

    def _embed(self, text: str) -> list[float]:
        return [ord(c) / 1000 for c in text[:10]]

    def query(self, question: str) -> str:
        retrieved = self._retrieve(question)
        texts = [self.nodes[i]["text"] for i in retrieved]
        return f"[LlamaIndex] 从索引中检索{len(retrieved)}个节点"

    def _retrieve(self, query: str, top_k: int = 3) -> list[int]:
        scores = {}
        for char in query:
            for node_id in self.index.get(char, []):
                scores[node_id] = scores.get(node_id, 0) + 1
        sorted_ids = sorted(scores, key=scores.get, reverse=True)
        return sorted_ids[:top_k]


# ============================================================
# Haystack风格：Pipeline模块化
# ============================================================
class HaystackStyleRAG:
    """模拟Haystack的Pipeline模块化设计"""

    def __init__(self):
        self.document_store = []
        self.pipeline_steps = []

    def add_to_store(self, docs: list[str]):
        for doc in docs:
            self.document_store.append({"content": doc})

    def build_pipeline(self):
        self.pipeline_steps = ["retriever", "prompt_builder", "generator"]

    def run(self, query: str) -> dict:
        self.build_pipeline()
        result = {"query": query}
        for step in self.pipeline_steps:
            result = self._execute_step(step, result)
        return result

    def _execute_step(self, step: str, data: dict) -> dict:
        if step == "retriever":
            data["documents"] = self.document_store[:3]
        elif step == "prompt_builder":
            ctx = "\n".join([d["content"] for d in data.get("documents", [])])
            data["prompt"] = f"Context: {ctx}\nQuery: {data['query']}"
        elif step == "generator":
            data["answer"] = f"[Haystack] Pipeline执行完成，经过{len(self.pipeline_steps)}个步骤"
        return data


# ============================================================
# 对比演示
# ============================================================
def main():
    print("=" * 60)
    print("AI应用框架对比演示")
    print("=" * 60)

    # 准备测试数据
    documents = [
        "RAG（检索增强生成）是一种结合检索和生成的AI架构模式",
        "LangChain是一个通用的LLM应用编排框架，支持Chain和Agent",
        "LlamaIndex专注于数据索引和检索，适合知识问答场景",
        "Haystack是一个模块化的NLP Pipeline框架",
        "向量数据库用于存储和检索高维向量数据",
    ]
    query = "什么是RAG架构？"

    # 1. LangChain风格
    print("\n--- LangChain风格 ---")
    lc = LangChainStyleRAG()
    lc.load_documents(documents)
    result = lc.chain(query)
    print(f"查询: {query}")
    print(f"结果: {result}")

    # 2. LlamaIndex风格
    print("\n--- LlamaIndex风格 ---")
    li = LlamaIndexStyleRAG()
    li.build_index(documents)
    result = li.query(query)
    print(f"查询: {query}")
    print(f"结果: {result}")

    # 3. Haystack风格
    print("\n--- Haystack风格 ---")
    hs = HaystackStyleRAG()
    hs.add_to_store(documents)
    result = hs.run(query)
    print(f"查询: {query}")
    print(f"结果: {result['answer']}")

    # 对比总结
    print("\n" + "=" * 60)
    print("框架对比总结")
    print("=" * 60)
    comparison = [
        ("LangChain", "Chain式编排", "Agent+复杂链", "陡峭"),
        ("LlamaIndex", "Index优先", "RAG+知识问答", "中等"),
        ("Haystack", "Pipeline模块化", "搜索+文档处理", "平缓"),
    ]
    print(f"{'框架':<15} {'设计模式':<15} {'适用场景':<20} {'学习曲线'}")
    print("-" * 65)
    for name, pattern, scene, curve in comparison:
        print(f"{name:<15} {pattern:<15} {scene:<20} {curve}")


if __name__ == "__main__":
    main()
