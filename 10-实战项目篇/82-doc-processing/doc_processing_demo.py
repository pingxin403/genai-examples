"""
文档智能处理演示：OCR + 表格识别 + RAG流水线
对应文章：82-文档智能处理OCR加表格识别加RAG的流水线
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ProcessedDocument:
    doc_id: str
    doc_type: str
    raw_text: str
    structured_data: dict = field(default_factory=dict)
    chunks: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class DocumentClassifier:
    """文档分类器"""

    RULES = {
        "invoice": ["发票", "税额", "价税合计", "纳税人", "开票"],
        "contract": ["合同", "甲方", "乙方", "签章", "违约"],
        "report": ["报表", "季度", "同比", "环比", "营收"],
        "manual": ["手册", "使用说明", "操作指南", "步骤"],
    }

    def classify(self, text: str) -> tuple[str, float]:
        scores = {}
        for doc_type, keywords in self.RULES.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[doc_type] = score
        best = max(scores, key=scores.get)
        total = len(self.RULES.get(best, []))
        confidence = scores[best] / total if total > 0 and scores[best] > 0 else 0
        return (best, round(confidence, 2)) if confidence > 0 else ("unknown", 0.0)


class OCRSimulator:
    """OCR模拟器"""

    def extract(self, doc_name: str) -> str:
        mock_docs = {
            "invoice_001.pdf": (
                "增值税电子普通发票\n"
                "发票号码：12345678\n"
                "开票日期：2024-10-15\n"
                "销售方：ABC科技有限公司\n"
                "购买方：XYZ集团\n"
                "项目 | 数量 | 单价 | 金额\n"
                "云服务费 | 1 | 50000.00 | 50000.00\n"
                "技术支持 | 12 | 2000.00 | 24000.00\n"
                "税额：9620.00\n"
                "价税合计：¥83620.00\n"
            ),
            "contract_001.pdf": (
                "技术服务合同\n"
                "合同编号：HT-2024-001\n"
                "甲方：XYZ集团有限公司\n"
                "乙方：ABC科技有限公司\n"
                "第一条 服务内容\n"
                "乙方为甲方提供AI平台建设服务。\n"
                "第二条 服务期限\n"
                "自2024年1月1日至2024年12月31日。\n"
                "第三条 违约责任\n"
                "任何一方违约需支付合同金额10%的违约金。\n"
            ),
            "report_q3.pdf": (
                "2024年Q3财务报表\n"
                "指标 | Q3 | Q2 | 同比\n"
                "营收 | 1.2亿 | 1.0亿 | +20%\n"
                "净利润 | 2160万 | 1800万 | +20%\n"
                "毛利率 | 65% | 62% | +3pp\n"
                "季度总结：Q3业绩超预期完成。\n"
            ),
        }
        return mock_docs.get(doc_name, f"[无法识别的文档: {doc_name}]")


class TableExtractor:
    """表格识别与提取"""

    def extract(self, text: str) -> list[dict]:
        tables = []
        lines = text.strip().split("\n")
        current_table = []

        for line in lines:
            if "|" in line:
                cells = [c.strip() for c in line.split("|") if c.strip()]
                if cells:
                    current_table.append(cells)
            else:
                if len(current_table) >= 2:
                    tables.append(self._parse_table(current_table))
                current_table = []

        if len(current_table) >= 2:
            tables.append(self._parse_table(current_table))
        return tables

    def _parse_table(self, rows: list[list]) -> dict:
        headers = rows[0]
        data = []
        for row in rows[1:]:
            if len(row) == len(headers):
                data.append(dict(zip(headers, row)))
        return {"headers": headers, "rows": data, "row_count": len(data)}


class InvoiceExtractor:
    """发票信息提取"""

    FIELDS = {
        "invoice_no": r"发票号码[：:]\s*(\d+)",
        "date": r"开票日期[：:]\s*([\d-]+)",
        "amount": r"价税合计[：:]\s*[¥￥]?([\d,.]+)",
        "seller": r"销售方[：:]\s*(.+)",
        "buyer": r"购买方[：:]\s*(.+)",
        "tax": r"税额[：:]\s*[¥￥]?([\d,.]+)",
    }

    def extract(self, text: str) -> dict:
        result = {}
        for name, pattern in self.FIELDS.items():
            match = re.search(pattern, text)
            if match:
                result[name] = match.group(1).strip()
        return result


class DocumentChunker:
    """文档分块器"""

    def chunk(self, doc: ProcessedDocument) -> list[dict]:
        if doc.doc_type == "invoice":
            return [{"type": "invoice_data",
                      "content": str(doc.structured_data),
                      "metadata": doc.metadata}]
        elif doc.doc_type == "contract":
            return self._chunk_by_section(doc.raw_text, doc.metadata)
        else:
            return self._chunk_by_size(doc.raw_text, 200, doc.metadata)

    def _chunk_by_section(self, text: str, metadata: dict) -> list[dict]:
        sections = re.split(r"(第[一二三四五六七八九十]+条)", text)
        chunks = []
        for i in range(1, len(sections), 2):
            title = sections[i]
            content = sections[i + 1].strip() if i + 1 < len(sections) else ""
            chunks.append({
                "type": "contract_section",
                "title": title,
                "content": f"{title} {content}",
                "metadata": metadata,
            })
        if not chunks:
            chunks.append({"type": "full_text", "content": text[:500],
                           "metadata": metadata})
        return chunks

    def _chunk_by_size(self, text: str, size: int, metadata: dict) -> list[dict]:
        chunks = []
        for i in range(0, len(text), size):
            chunks.append({
                "type": "text_chunk",
                "content": text[i:i + size],
                "metadata": metadata,
            })
        return chunks


class DocumentPipeline:
    """文档处理流水线"""

    def __init__(self):
        self.classifier = DocumentClassifier()
        self.ocr = OCRSimulator()
        self.table_extractor = TableExtractor()
        self.invoice_extractor = InvoiceExtractor()
        self.chunker = DocumentChunker()
        self.knowledge_base: list[dict] = []

    def process(self, doc_name: str) -> ProcessedDocument:
        # 1. OCR提取
        raw_text = self.ocr.extract(doc_name)

        # 2. 文档分类
        doc_type, confidence = self.classifier.classify(raw_text)

        doc = ProcessedDocument(
            doc_id=doc_name.replace(".", "_"),
            doc_type=doc_type,
            raw_text=raw_text,
            metadata={"source": doc_name, "type": doc_type,
                       "confidence": confidence},
        )

        # 3. 结构化提取
        tables = self.table_extractor.extract(raw_text)
        if tables:
            doc.structured_data["tables"] = tables

        if doc_type == "invoice":
            invoice_data = self.invoice_extractor.extract(raw_text)
            doc.structured_data["invoice"] = invoice_data

        # 4. 分块
        doc.chunks = self.chunker.chunk(doc)

        # 5. 入库
        for chunk in doc.chunks:
            self.knowledge_base.append(chunk)

        return doc


def main():
    pipeline = DocumentPipeline()

    print("=" * 60)
    print("文档智能处理Pipeline演示")
    print("=" * 60)

    docs = ["invoice_001.pdf", "contract_001.pdf", "report_q3.pdf"]

    for doc_name in docs:
        print(f"\n{'='*40}")
        print(f"处理文档: {doc_name}")
        print(f"{'='*40}")

        result = pipeline.process(doc_name)

        # 分类结果
        print(f"\n  --- 分类 ---")
        print(f"  类型: {result.doc_type} "
              f"(置信度: {result.metadata['confidence']})")

        # 表格提取
        tables = result.structured_data.get("tables", [])
        if tables:
            print(f"\n  --- 表格识别 ({len(tables)}个) ---")
            for i, t in enumerate(tables):
                print(f"  表格{i+1}: {t['headers']} ({t['row_count']}行)")
                for row in t["rows"][:2]:
                    print(f"    {row}")

        # 发票信息
        invoice = result.structured_data.get("invoice", {})
        if invoice:
            print(f"\n  --- 发票信息 ---")
            for k, v in invoice.items():
                print(f"  {k}: {v}")

        # 分块结果
        print(f"\n  --- 分块 ({len(result.chunks)}个) ---")
        for chunk in result.chunks[:3]:
            print(f"  [{chunk['type']}] {chunk['content'][:60]}...")

    # 知识库统计
    print(f"\n{'='*40}")
    print(f"知识库统计")
    print(f"{'='*40}")
    print(f"  总chunk数: {len(pipeline.knowledge_base)}")
    types = {}
    for chunk in pipeline.knowledge_base:
        t = chunk["type"]
        types[t] = types.get(t, 0) + 1
    for t, count in types.items():
        print(f"  {t}: {count}个")


if __name__ == "__main__":
    main()
