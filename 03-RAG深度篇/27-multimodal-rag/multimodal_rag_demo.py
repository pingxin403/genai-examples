"""
多模态RAG演示
=============
配套文章：多模态RAG：当图片、表格也成为检索对象

演示内容：
1. 图片描述生成（Image Captioning for Retrieval）
2. 表格理解与结构化（Table Understanding）
3. 跨模态统一索引与检索（Cross-Modal Index & Search）
4. 完整多模态RAG Pipeline

运行方式：python multimodal_rag_demo.py
依赖：Python 3.10+，无外部依赖
"""

import hashlib
import math
import random
from dataclasses import dataclass, field


# ============================================================
# 第一部分：图片描述生成
# ============================================================

@dataclass
class ImageAsset:
    """图片资产"""
    image_id: str
    source_doc: str
    page_number: int
    image_type: str  # chart / diagram / screenshot / table_image
    raw_path: str = ""
    caption: str = ""
    embedding: list[float] = field(default_factory=list)


class ImageCaptioner:
    """图片描述生成器 - 按类型定制Prompt生成检索友好的描述"""

    CAPTION_PROMPTS = {
        "chart": "请详细描述这张图表的数据趋势、关键数值和结论",
        "diagram": "请描述这张架构图/流程图的组件、连接关系和数据流向",
        "screenshot": "请描述这张截图中的界面元素、操作步骤和关键信息",
        "table_image": "请逐行逐列描述这张表格的表头和数据内容",
    }

    # 模拟不同类型图片的描述输出
    MOCK_CAPTIONS = {
        "chart": "柱状图展示2024年各季度营收：Q1为2.3亿元，Q2为2.8亿元，Q3为3.1亿元，Q4预测3.5亿元。整体呈上升趋势，Q3同比增长15%。",
        "diagram": "微服务架构图包含5个核心服务：API网关→用户服务、订单服务、支付服务、通知服务。订单服务调用支付服务和库存服务，支付服务通过MQ异步通知订单服务。",
        "screenshot": "后台管理界面截图，左侧导航栏包含：仪表盘、用户管理、订单管理、系统设置。主区域显示订单列表，包含订单号、金额、状态、创建时间等列。",
        "table_image": "产品对比表格：产品A月活100万、营收500万、增长率20%；产品B月活80万、营收350万、增长率15%；产品C月活50万、营收200万、增长率30%。",
    }

    def generate_caption(self, image: ImageAsset) -> str:
        """为图片生成检索友好的文本描述"""
        prompt = self.CAPTION_PROMPTS.get(image.image_type, "请描述这张图片的内容")
        # 实际生产中：caption = vlm.generate(image=image.raw_path, prompt=prompt)
        caption = self.MOCK_CAPTIONS.get(image.image_type, f"图片来自{image.source_doc}第{image.page_number}页")
        image.caption = caption
        return caption

    def batch_caption(self, images: list[ImageAsset]) -> list[str]:
        """批量生成图片描述"""
        return [self.generate_caption(img) for img in images]


# ============================================================
# 第二部分：表格理解与结构化
# ============================================================

@dataclass
class TableAsset:
    """表格资产"""
    table_id: str
    source_doc: str
    page_number: int
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    summary: str = ""
    markdown: str = ""
    embedding: list[float] = field(default_factory=list)


class TableUnderstanding:
    """表格理解引擎 - 结构化解析 + 自然语言摘要"""

    def parse_to_structured(self, table: TableAsset) -> TableAsset:
        """将表格解析为Markdown格式 + 生成自然语言摘要"""
        # 生成Markdown格式（保留结构信息）
        if table.headers and table.rows:
            md_lines = ["| " + " | ".join(table.headers) + " |"]
            md_lines.append("| " + " | ".join(["---"] * len(table.headers)) + " |")
            for row in table.rows:
                md_lines.append("| " + " | ".join(row) + " |")
            table.markdown = "\n".join(md_lines)

        # 生成自然语言摘要（用于Embedding检索）
        table.summary = self._generate_summary(table)
        return table

    def _generate_summary(self, table: TableAsset) -> str:
        """生成表格的自然语言摘要"""
        if not table.headers:
            return f"来自{table.source_doc}第{table.page_number}页的表格"

        col_desc = "、".join(table.headers[:5])
        row_count = len(table.rows)

        # 提取关键数据点
        data_points = []
        for row in table.rows[:3]:
            if len(row) >= 2:
                data_points.append(f"{row[0]}({row[1]})")

        summary = f"表格包含{row_count}行数据，列包括：{col_desc}。"
        if data_points:
            summary += f"主要数据：{'、'.join(data_points)}。"
        summary += f"来源：{table.source_doc}第{table.page_number}页"
        return summary

    def query_table(self, table: TableAsset, column: str, row_filter: str = "") -> list[dict]:
        """在表格中查询特定数据"""
        if column not in table.headers:
            return []
        col_idx = table.headers.index(column)
        results = []
        for row in table.rows:
            if row_filter and row_filter not in str(row):
                continue
            result = {table.headers[i]: row[i] for i in range(len(row))}
            results.append(result)
        return results


# ============================================================
# 第三部分：跨模态统一索引与检索
# ============================================================

@dataclass
class MultimodalChunk:
    """多模态检索单元"""
    chunk_id: str
    content_type: str  # text / image / table
    text_content: str  # 文本内容 或 图片描述 或 表格摘要
    raw_content: str = ""  # 原始内容（图片路径/表格Markdown）
    source_doc: str = ""
    page_number: int = 0
    embedding: list[float] = field(default_factory=list)
    relevance_score: float = 0.0


class MultimodalIndex:
    """多模态统一索引 - 文本、图片、表格统一检索"""

    def __init__(self):
        self.chunks: list[MultimodalChunk] = []

    def add_text(self, chunk_id: str, text: str, source_doc: str, page: int):
        """添加文本块"""
        chunk = MultimodalChunk(
            chunk_id=chunk_id, content_type="text",
            text_content=text, source_doc=source_doc, page_number=page,
            embedding=self._compute_embedding(text),
        )
        self.chunks.append(chunk)

    def add_image(self, chunk_id: str, caption: str, image_path: str,
                  source_doc: str, page: int):
        """添加图片（通过描述文本索引）"""
        chunk = MultimodalChunk(
            chunk_id=chunk_id, content_type="image",
            text_content=caption, raw_content=image_path,
            source_doc=source_doc, page_number=page,
            embedding=self._compute_embedding(caption),
        )
        self.chunks.append(chunk)

    def add_table(self, chunk_id: str, summary: str, markdown: str,
                  source_doc: str, page: int):
        """添加表格（通过摘要文本索引）"""
        chunk = MultimodalChunk(
            chunk_id=chunk_id, content_type="table",
            text_content=summary, raw_content=markdown,
            source_doc=source_doc, page_number=page,
            embedding=self._compute_embedding(summary),
        )
        self.chunks.append(chunk)

    def search(self, query: str, top_k: int = 5,
               type_weights: dict = None) -> list[MultimodalChunk]:
        """跨模态检索 + 类型加权"""
        if type_weights is None:
            type_weights = {"text": 1.0, "image": 0.9, "table": 0.95}

        query_emb = self._compute_embedding(query)
        for chunk in self.chunks:
            base_score = self._cosine_similarity(query_emb, chunk.embedding)
            weight = type_weights.get(chunk.content_type, 1.0)
            chunk.relevance_score = base_score * weight

        results = sorted(self.chunks, key=lambda c: c.relevance_score, reverse=True)
        return results[:top_k]

    def stats(self) -> dict:
        """索引统计"""
        type_counts = {}
        for chunk in self.chunks:
            type_counts[chunk.content_type] = type_counts.get(chunk.content_type, 0) + 1
        return {"total_chunks": len(self.chunks), "by_type": type_counts}

    def _compute_embedding(self, text: str) -> list[float]:
        """模拟Embedding生成（实际用text-embedding-3-small等模型）"""
        h = hashlib.sha256(text.encode()).hexdigest()
        return [int(h[i:i + 2], 16) / 255.0 for i in range(0, 32, 2)]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """余弦相似度"""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)



# ============================================================
# 第四部分：完整多模态RAG Pipeline
# ============================================================

class MultimodalRAGPipeline:
    """完整多模态RAG Pipeline：解析 → 索引 → 检索 → 生成"""

    def __init__(self):
        self.captioner = ImageCaptioner()
        self.table_engine = TableUnderstanding()
        self.index = MultimodalIndex()
        self.query_log: list[dict] = []

    def ingest_document(self, doc_name: str, text_chunks: list[dict],
                        images: list[ImageAsset], tables: list[TableAsset]):
        """摄入一份多模态文档"""
        # 1. 索引文本块
        for tc in text_chunks:
            self.index.add_text(
                chunk_id=tc["id"], text=tc["text"],
                source_doc=doc_name, page=tc.get("page", 0),
            )

        # 2. 图片描述生成 + 索引
        for img in images:
            caption = self.captioner.generate_caption(img)
            self.index.add_image(
                chunk_id=img.image_id, caption=caption,
                image_path=img.raw_path,
                source_doc=doc_name, page=img.page_number,
            )

        # 3. 表格结构化 + 索引
        for tbl in tables:
            self.table_engine.parse_to_structured(tbl)
            self.index.add_table(
                chunk_id=tbl.table_id, summary=tbl.summary,
                markdown=tbl.markdown,
                source_doc=doc_name, page=tbl.page_number,
            )

    def query(self, question: str, top_k: int = 3) -> dict:
        """多模态RAG查询"""
        # 1. 跨模态检索
        results = self.index.search(question, top_k=top_k)

        # 2. 组装上下文（根据类型选择不同内容）
        context_parts = []
        for r in results:
            if r.content_type == "table" and r.raw_content:
                # 表格：传完整Markdown而非摘要
                context_parts.append(f"[表格]\n{r.raw_content}")
            elif r.content_type == "image":
                context_parts.append(f"[图片描述] {r.text_content}")
            else:
                context_parts.append(f"[文本] {r.text_content}")
        context = "\n\n".join(context_parts)

        # 3. 模拟LLM生成（实际调用GPT-4o等）
        answer = f"基于检索到的{len(results)}条多模态内容回答：{question}"

        # 4. 记录查询日志
        log_entry = {
            "question": question,
            "retrieved_types": [r.content_type for r in results],
            "top_score": round(results[0].relevance_score, 4) if results else 0,
            "context_length": len(context),
        }
        self.query_log.append(log_entry)

        return {
            "answer": answer,
            "sources": [
                {
                    "type": r.content_type,
                    "source": r.source_doc,
                    "page": r.page_number,
                    "score": round(r.relevance_score, 4),
                }
                for r in results
            ],
            "context_length": len(context),
        }


# ============================================================
# 演示入口
# ============================================================

def demo_image_captioning():
    """演示1：图片描述生成"""
    print("\n--- 1. 图片描述生成 ---")
    captioner = ImageCaptioner()

    images = [
        ImageAsset("img_001", "2024年度财报.pdf", 5, "chart", "/images/revenue_chart.png"),
        ImageAsset("img_002", "系统架构文档.pdf", 3, "diagram", "/images/arch_diagram.png"),
        ImageAsset("img_003", "操作手册.pdf", 12, "screenshot", "/images/admin_panel.png"),
        ImageAsset("img_004", "产品对比报告.pdf", 8, "table_image", "/images/product_table.png"),
    ]

    for img in images:
        caption = captioner.generate_caption(img)
        print(f"  [{img.image_type}] {img.source_doc} P{img.page_number}")
        print(f"    描述: {caption[:60]}...")


def demo_table_understanding():
    """演示2：表格理解与结构化"""
    print("\n--- 2. 表格理解与结构化 ---")
    engine = TableUnderstanding()

    table = TableAsset(
        table_id="tbl_001",
        source_doc="2024年度财报.pdf",
        page_number=10,
        headers=["产品线", "Q3营收(万)", "同比增长", "毛利率"],
        rows=[
            ["企业服务", "3100", "15%", "62%"],
            ["消费业务", "2800", "8%", "45%"],
            ["云计算", "1500", "25%", "38%"],
            ["广告业务", "900", "3%", "72%"],
        ],
    )

    engine.parse_to_structured(table)
    print(f"  表格ID: {table.table_id}")
    print(f"  Markdown格式:\n{table.markdown}")
    print(f"  自然语言摘要: {table.summary}")

    # 表格内查询
    results = engine.query_table(table, "Q3营收(万)", "企业服务")
    print(f"  查询'企业服务的Q3营收': {results}")


def demo_cross_modal_search():
    """演示3：跨模态统一索引与检索"""
    print("\n--- 3. 跨模态统一索引与检索 ---")
    index = MultimodalIndex()

    # 添加不同模态的内容
    index.add_text("txt_001", "公司2024年Q3营收达到8300万，同比增长12%。", "财报.pdf", 2)
    index.add_text("txt_002", "系统采用微服务架构，核心服务包括用户、订单、支付模块。", "架构文档.pdf", 1)
    index.add_image("img_001", "柱状图展示2024年各季度营收：Q1为2.3亿，Q2为2.8亿，Q3为3.1亿", "/chart.png", "财报.pdf", 5)
    index.add_table("tbl_001", "产品对比表：企业服务营收3100万增长15%，消费业务2800万增长8%", "| 产品 | 营收 |\n|---|---|\n| 企业服务 | 3100万 |", "财报.pdf", 10)

    print(f"  索引统计: {index.stats()}")

    # 跨模态检索
    queries = ["Q3营收是多少", "系统架构是什么样的", "各产品线的营收对比"]
    for q in queries:
        results = index.search(q, top_k=2)
        print(f"\n  查询: '{q}'")
        for r in results:
            print(f"    [{r.content_type}] score={r.relevance_score:.4f} | {r.text_content[:40]}...")


def demo_full_pipeline():
    """演示4：完整多模态RAG Pipeline"""
    print("\n--- 4. 完整多模态RAG Pipeline ---")
    pipeline = MultimodalRAGPipeline()

    # 摄入一份多模态文档
    text_chunks = [
        {"id": "txt_001", "text": "2024年第三季度，公司总营收达到8300万元，同比增长12%。", "page": 2},
        {"id": "txt_002", "text": "企业服务板块持续增长，成为公司核心收入来源。", "page": 3},
        {"id": "txt_003", "text": "公司研发投入占营收比例为18%，重点投入AI和云计算方向。", "page": 6},
    ]
    images = [
        ImageAsset("img_001", "2024Q3财报.pdf", 5, "chart", "/images/revenue.png"),
        ImageAsset("img_002", "2024Q3财报.pdf", 8, "diagram", "/images/biz_structure.png"),
    ]
    tables = [
        TableAsset(
            table_id="tbl_001", source_doc="2024Q3财报.pdf", page_number=10,
            headers=["产品线", "营收(万)", "同比增长", "占比"],
            rows=[
                ["企业服务", "3100", "15%", "37%"],
                ["消费业务", "2800", "8%", "34%"],
                ["云计算", "1500", "25%", "18%"],
                ["广告", "900", "3%", "11%"],
            ],
        ),
    ]

    pipeline.ingest_document("2024Q3财报.pdf", text_chunks, images, tables)
    stats = pipeline.index.stats()
    print(f"  文档摄入完成: {stats}")

    # 多模态查询
    questions = [
        "Q3总营收是多少？",
        "各产品线的营收占比情况？",
        "公司的业务架构是什么样的？",
    ]
    for q in questions:
        result = pipeline.query(q, top_k=3)
        types = [s["type"] for s in result["sources"]]
        top_score = result["sources"][0]["score"] if result["sources"] else 0
        print(f"\n  Q: {q}")
        print(f"    检索类型: {types} | 最高分: {top_score} | 上下文长度: {result['context_length']}")
        for s in result["sources"]:
            print(f"      [{s['type']}] {s['source']} P{s['page']} (score={s['score']})")


if __name__ == "__main__":
    print("=" * 55)
    print("  多模态RAG演示")
    print("=" * 55)

    random.seed(42)

    demo_image_captioning()
    demo_table_understanding()
    demo_cross_modal_search()
    demo_full_pipeline()

    print("\n" + "=" * 55)
    print("  演示完成！")
    print("=" * 55)
