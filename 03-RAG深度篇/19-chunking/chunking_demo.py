"""
分块（Chunking）策略实战演示
配套文章：《分块（Chunking）的艺术：语义边界vs固定大小》

演示四种主流分块策略：
1. 固定大小分块（Fixed-Size Chunking）
2. 递归字符分块（Recursive Character Chunking）
3. 语义分块（Semantic Chunking）
4. 文档结构分块（Structure-Aware Chunking）
"""

import re
import numpy as np


# ============================================================
# 策略1：固定大小分块
# ============================================================

def fixed_size_chunking(text: str, chunk_size: int = 500,
                        overlap: int = 50) -> list[dict]:
    """
    固定大小分块：按字符数等间隔切割
    - chunk_size: 每个块的字符数
    - overlap: 相邻块的重叠字符数
    """
    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]

        chunks.append({
            "id": chunk_id,
            "text": chunk_text.strip(),
            "start": start,
            "end": min(end, len(text)),
            "strategy": "fixed_size"
        })

        chunk_id += 1
        start += chunk_size - overlap

    return [c for c in chunks if c["text"]]


# ============================================================
# 策略2：递归字符分块
# ============================================================

class RecursiveChunker:
    """按分隔符优先级递归分块，尽量保留段落完整性"""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = ["\n\n", "\n", "。", "！", "？", ".", "!", "?",
                           "；", ";", "，", ",", " "]

    def chunk(self, text: str) -> list[dict]:
        return self._recursive_split(text, self.separators)

    def _recursive_split(self, text: str, separators: list) -> list[dict]:
        if len(text) <= self.chunk_size:
            return [{"text": text.strip(), "strategy": "recursive"}] if text.strip() else []

        for sep in separators:
            if sep in text:
                parts = text.split(sep)
                chunks = []
                current = ""

                for part in parts:
                    candidate = current + sep + part if current else part
                    if len(candidate) <= self.chunk_size:
                        current = candidate
                    else:
                        if current.strip():
                            chunks.append({"text": current.strip(),
                                           "strategy": "recursive"})
                        current = part

                if current.strip():
                    chunks.append({"text": current.strip(),
                                   "strategy": "recursive"})
                return chunks

        # 所有分隔符都不适用，强制按大小切割
        return [{"text": text[i:i + self.chunk_size].strip(),
                 "strategy": "recursive_forced"}
                for i in range(0, len(text), self.chunk_size - self.overlap)
                if text[i:i + self.chunk_size].strip()]


# ============================================================
# 策略3：语义分块
# ============================================================

class SemanticChunker:
    """基于embedding相似度检测语义边界的智能分块"""

    def __init__(self, similarity_threshold: float = 0.5,
                 min_chunk_size: int = 100):
        self.threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str) -> list[dict]:
        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return [{"text": text, "strategy": "semantic"}]

        embeddings = [self._get_embedding(s) for s in sentences]
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)

        # 在相似度低谷处切分
        chunks = []
        current_sentences = [sentences[0]]

        for i, sim in enumerate(similarities):
            if sim < self.threshold and \
               len("".join(current_sentences)) >= self.min_chunk_size:
                chunks.append({
                    "text": "".join(current_sentences).strip(),
                    "strategy": "semantic",
                    "boundary_similarity": round(sim, 3)
                })
                current_sentences = [sentences[i + 1]]
            else:
                current_sentences.append(sentences[i + 1])

        if current_sentences:
            chunks.append({
                "text": "".join(current_sentences).strip(),
                "strategy": "semantic"
            })

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        return [s for s in re.split(r'(?<=[。！？.!?\n])', text) if s.strip()]

    def _get_embedding(self, text: str) -> list[float]:
        """模拟embedding（实际项目中替换为真实embedding API调用）"""
        np.random.seed(hash(text) % (2 ** 32))
        return np.random.rand(128).tolist()

    def _cosine_similarity(self, a: list, b: list) -> float:
        a_arr, b_arr = np.array(a), np.array(b)
        return float(np.dot(a_arr, b_arr) /
                     (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


# ============================================================
# 策略4：文档结构分块
# ============================================================

class StructureChunker:
    """基于Markdown标题层级的文档结构分块"""

    def chunk(self, markdown_text: str,
              max_chunk_size: int = 1000) -> list[dict]:
        sections = self._split_by_headers(markdown_text)
        chunks = []

        for section in sections:
            if len(section["content"]) <= max_chunk_size:
                chunks.append({
                    "text": section["content"].strip(),
                    "strategy": "structure",
                    "heading": section["heading"],
                    "level": section["level"]
                })
            else:
                sub_chunker = RecursiveChunker(chunk_size=max_chunk_size)
                sub_chunks = sub_chunker.chunk(section["content"])
                for sc in sub_chunks:
                    sc["heading"] = section["heading"]
                    sc["level"] = section["level"]
                    chunks.append(sc)

        return [c for c in chunks if c["text"]]

    def _split_by_headers(self, text: str) -> list[dict]:
        pattern = r'^(#{1,6})\s+(.+)$'
        lines = text.split("\n")
        sections = []
        current = {"heading": "文档开头", "level": 0, "content": ""}

        for line in lines:
            match = re.match(pattern, line)
            if match:
                if current["content"].strip():
                    sections.append(current)
                current = {
                    "heading": match.group(2).strip(),
                    "level": len(match.group(1)),
                    "content": line + "\n"
                }
            else:
                current["content"] += line + "\n"

        if current["content"].strip():
            sections.append(current)

        return sections


# ============================================================
# 元数据标注工具
# ============================================================

def add_metadata(chunks: list[dict], source: str,
                 doc_type: str = "unknown") -> list[dict]:
    """为每个chunk添加元数据，方便溯源和过滤"""
    for i, chunk in enumerate(chunks):
        chunk["metadata"] = {
            "source": source,
            "doc_type": doc_type,
            "chunk_index": i,
            "char_count": len(chunk["text"]),
            "strategy": chunk.get("strategy", "unknown")
        }
    return chunks


# ============================================================
# 演示主程序
# ============================================================

def main():
    # 示例文本：模拟一篇技术文档
    sample_text = """
RAG系统的核心组件包括文档解析、分块、向量化和检索四个环节。其中分块策略的选择直接影响检索质量。

文档解析是第一步。我们需要从PDF、Word、HTML等格式中提取纯文本。不同格式的解析难度差异很大，PDF中的表格提取尤其困难。

分块是第二步。分块的目标是将长文档切成适合embedding的小段落。常见策略包括固定大小分块、递归字符分块、语义分块和文档结构分块。每种策略都有其适用场景。

向量化是第三步。选择合适的embedding模型将文本块转为向量。模型的选择需要考虑语言支持、维度大小、推理速度等因素。

检索是最后一步。用户提问时，系统将query向量化后在向量库中搜索最相似的chunk。检索质量取决于分块质量和embedding质量的共同作用。

在实际项目中，我发现分块策略对最终效果的影响往往被低估。很多团队花大量时间调优Prompt和模型，却忽略了分块这个基础环节。一个好的分块策略，能让召回率提升20%以上。
""".strip()

    # Markdown示例文本
    markdown_text = """# RAG系统架构

## 文档解析
从PDF、Word、HTML等格式中提取纯文本。不同格式的解析难度差异很大。

## 分块策略
将长文档切成适合embedding的小段落。常见策略包括固定大小、递归字符、语义分块。

### 固定大小分块
按字符数等间隔切割，实现简单但可能切断语义。

### 语义分块
基于embedding相似度检测语义边界，效果好但计算成本高。

## 向量化
选择合适的embedding模型将文本块转为向量。

## 检索
用户提问时搜索最相似的chunk返回给模型。
""".strip()

    print("=" * 60)
    print("🧩 分块（Chunking）策略对比演示")
    print("=" * 60)

    # --- 策略1：固定大小分块 ---
    print("\n📌 策略1：固定大小分块（chunk_size=200, overlap=30）")
    print("-" * 40)
    chunks_fixed = fixed_size_chunking(sample_text, chunk_size=200, overlap=30)
    chunks_fixed = add_metadata(chunks_fixed, "sample.txt", "plain_text")
    for c in chunks_fixed:
        print(f"  Chunk {c['id']}: [{c['start']}:{c['end']}] "
              f"({len(c['text'])}字符)")
        print(f"    {c['text'][:60]}...")
    print(f"  → 共 {len(chunks_fixed)} 个chunk")

    # --- 策略2：递归字符分块 ---
    print("\n📌 策略2：递归字符分块（chunk_size=200）")
    print("-" * 40)
    chunker_recursive = RecursiveChunker(chunk_size=200)
    chunks_recursive = chunker_recursive.chunk(sample_text)
    chunks_recursive = add_metadata(chunks_recursive, "sample.txt", "plain_text")
    for i, c in enumerate(chunks_recursive):
        print(f"  Chunk {i}: ({len(c['text'])}字符)")
        print(f"    {c['text'][:60]}...")
    print(f"  → 共 {len(chunks_recursive)} 个chunk")

    # --- 策略3：语义分块 ---
    print("\n📌 策略3：语义分块（threshold=0.5）")
    print("-" * 40)
    chunker_semantic = SemanticChunker(similarity_threshold=0.5)
    chunks_semantic = chunker_semantic.chunk(sample_text)
    chunks_semantic = add_metadata(chunks_semantic, "sample.txt", "plain_text")
    for i, c in enumerate(chunks_semantic):
        sim_info = f", 边界相似度={c['boundary_similarity']}" \
            if 'boundary_similarity' in c else ""
        print(f"  Chunk {i}: ({len(c['text'])}字符{sim_info})")
        print(f"    {c['text'][:60]}...")
    print(f"  → 共 {len(chunks_semantic)} 个chunk")

    # --- 策略4：文档结构分块 ---
    print("\n📌 策略4：文档结构分块（Markdown标题层级）")
    print("-" * 40)
    chunker_structure = StructureChunker()
    chunks_structure = chunker_structure.chunk(markdown_text, max_chunk_size=300)
    chunks_structure = add_metadata(chunks_structure, "sample.md", "markdown")
    for i, c in enumerate(chunks_structure):
        heading = c.get("heading", "N/A")
        level = c.get("level", 0)
        print(f"  Chunk {i}: [H{level}] {heading} ({len(c['text'])}字符)")
        print(f"    {c['text'][:60]}...")
    print(f"  → 共 {len(chunks_structure)} 个chunk")

    # --- 汇总对比 ---
    print("\n" + "=" * 60)
    print("📊 策略效果汇总")
    print("=" * 60)
    strategies = [
        ("固定大小", chunks_fixed),
        ("递归字符", chunks_recursive),
        ("语义分块", chunks_semantic),
        ("文档结构", chunks_structure),
    ]
    print(f"{'策略':<10} {'chunk数':<10} {'平均大小':<12} {'最大':<8} {'最小':<8}")
    print("-" * 48)
    for name, chunks in strategies:
        sizes = [len(c["text"]) for c in chunks]
        avg_size = sum(sizes) / len(sizes) if sizes else 0
        max_size = max(sizes) if sizes else 0
        min_size = min(sizes) if sizes else 0
        print(f"{name:<10} {len(chunks):<10} {avg_size:<12.0f} "
              f"{max_size:<8} {min_size:<8}")


if __name__ == "__main__":
    main()
