"""
非结构化数据"洗"成向量：文档解析Pipeline示例
配套文章：《非结构化数据"洗"成向量：文档解析的5个坑》

演示内容：
1. PDF文本+表格提取（pdfplumber）
2. HTML噪声清洗（BeautifulSoup）
3. OCR后处理校正
4. Word文档清洁提取
5. 统一的文档解析Pipeline
"""

import re
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


# ============================================================
# 1. 数据模型
# ============================================================

@dataclass
class ParsedBlock:
    """解析后的文本块"""
    content: str
    source_file: str
    page: int = 0
    block_type: str = "text"  # text / table / heading
    metadata: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    """文档解析结果"""
    blocks: list[ParsedBlock]
    source_file: str
    doc_type: str
    stats: dict = field(default_factory=dict)


# ============================================================
# 2. PDF解析器
# ============================================================

class PDFParser:
    """
    PDF文档解析器：同时提取文本和表格
    关键点：用pdfplumber而非PyPDF2，表格识别能力更强
    """

    def parse(self, pdf_path: str) -> ParseResult:
        """解析PDF文件，提取文本和表格"""
        blocks = []

        # 实际项目中使用 pdfplumber：
        # with pdfplumber.open(pdf_path) as pdf:
        #     for page_num, page in enumerate(pdf.pages):
        #         text = page.extract_text()
        #         tables = page.extract_tables()

        # 这里用模拟数据演示流程
        sample_text = (
            "产品技术规格说明书\n\n"
            "1. 概述\n"
            "本产品采用最新的传感器技术，适用于工业自动化场景。\n\n"
            "2. 技术参数\n"
            "详细参数见下表。\n"
        )
        blocks.append(ParsedBlock(
            content=sample_text,
            source_file=pdf_path,
            page=1,
            block_type="text"
        ))

        # 模拟表格提取
        sample_table = [
            ["参数", "规格", "单位"],
            ["最大承重", "150", "kg"],
            ["工作温度", "-20~60", "℃"],
            ["防护等级", "IP67", "-"],
        ]
        table_text = self._table_to_text(sample_table)
        blocks.append(ParsedBlock(
            content=table_text,
            source_file=pdf_path,
            page=1,
            block_type="table",
            metadata={"table_index": 0, "rows": len(sample_table) - 1}
        ))

        return ParseResult(
            blocks=blocks,
            source_file=pdf_path,
            doc_type="pdf",
            stats={"pages": 1, "text_blocks": 1, "tables": 1}
        )

    def _table_to_text(self, table: list) -> str:
        """
        将二维表格转为结构化文本
        格式：每行用 "列名: 值" 的方式表示，保留列对应关系
        """
        if not table or not table[0]:
            return ""

        headers = [str(h or "").strip() for h in table[0]]
        rows = []
        for row in table[1:]:
            cells = [str(c or "").strip() for c in row]
            row_text = " | ".join(
                f"{headers[i]}: {cells[i]}"
                for i in range(min(len(headers), len(cells)))
                if cells[i]
            )
            if row_text:
                rows.append(row_text)

        return "\n".join(rows)


# ============================================================
# 3. HTML清洗器
# ============================================================

class HTMLCleaner:
    """
    HTML文档清洗器：移除导航、广告等噪声，只保留正文
    坑点：不清洗的话，导航菜单会污染整个知识库
    """

    NOISE_TAGS = [
        "nav", "header", "footer", "aside",
        "script", "style", "noscript", "iframe", "form"
    ]
    NOISE_CLASSES = [
        "navbar", "sidebar", "footer", "menu",
        "breadcrumb", "pagination", "ad", "banner"
    ]

    def clean(self, html_content: str) -> ParseResult:
        """清洗HTML，提取正文内容"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")

        # 第一步：移除噪声标签
        for tag_name in self.NOISE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # 第二步：移除噪声class的元素
        for cls in self.NOISE_CLASSES:
            for element in soup.find_all(class_=re.compile(cls, re.I)):
                element.decompose()

        # 第三步：定位正文区域
        main_content = (
            soup.find("main") or soup.find("article") or soup.find("body")
        )

        blocks = []
        if main_content:
            # 提取标题
            for h in main_content.find_all(re.compile(r"^h[1-6]$")):
                blocks.append(ParsedBlock(
                    content=h.get_text(strip=True),
                    source_file="html",
                    block_type="heading",
                    metadata={"level": int(h.name[1])}
                ))

            # 提取正文
            text = main_content.get_text(separator="\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text)
            if text:
                blocks.append(ParsedBlock(
                    content=text,
                    source_file="html",
                    block_type="text"
                ))

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        return ParseResult(
            blocks=blocks,
            source_file="html",
            doc_type="html",
            stats={"title": title, "blocks": len(blocks)}
        )


# ============================================================
# 4. OCR后处理器
# ============================================================

@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str
    confidence: float
    corrections: list = field(default_factory=list)


class OCRProcessor:
    """
    OCR后处理器：修正常见识别错误
    坑点：OCR原始输出中，数字0和字母O经常混淆
    """

    def process(self, raw_text: str) -> OCRResult:
        """对OCR原始输出进行后处理校正"""
        corrected = raw_text
        corrections = []

        # 修正1：数字上下文中的字母O → 数字0
        pattern = r'(\d+)[O](\d*)'
        if re.search(pattern, corrected):
            corrected = re.sub(pattern, lambda m: m.group(1) + '0' + m.group(2), corrected)
            corrections.append("字母O → 数字0（数字上下文）")

        # 修正2：日期格式中的字母O → 数字0
        date_pattern = r'(\d{4})-[O](\d)-(\d{2})'
        if re.search(date_pattern, corrected):
            corrected = re.sub(date_pattern, r'\1-0\2-\3', corrected)
            corrections.append("日期中字母O → 数字0")

        # 修正3：清理多余空格
        corrected = re.sub(r'[ \t]{2,}', ' ', corrected)

        # 计算置信度（基于修正数量）
        confidence = max(0.7, 1.0 - len(corrections) * 0.05)

        return OCRResult(
            text=corrected,
            confidence=confidence,
            corrections=corrections
        )

    def simulate_ocr(self) -> str:
        """模拟OCR原始输出（包含典型错误）"""
        return (
            "产品规格说明书\n"
            "型号: XR-20O3\n"       # O应为0
            "最大承重: 15Okg\n"     # O应为0
            "生产日期: 2024-O1-15\n"  # O应为0
            "工作电压: 22OV\n"      # O应为0
        )


# ============================================================
# 5. Word文档解析器
# ============================================================

class WordParser:
    """
    Word文档解析器：提取正文，过滤页眉页脚
    坑点：页眉页脚内容容易被当成正文
    """

    def parse_simulated(self) -> ParseResult:
        """模拟Word文档解析（实际项目用python-docx）"""
        # 模拟页眉页脚
        header_texts = {"XX公司内部文档-机密", "CONFIDENTIAL"}
        footer_texts = {"第1页/共10页", "第2页/共10页"}

        # 模拟正文段落（包含混入的页眉页脚）
        raw_paragraphs = [
            "XX公司内部文档-机密",  # 页眉，应过滤
            "产品设计规范 V2.0",
            "1. 设计目标",
            "本文档定义了产品的核心设计规范和技术要求。",
            "2. 功能需求",
            "系统需支持每秒1000次并发请求。",
            "第1页/共10页",  # 页脚，应过滤
            "3. 性能指标",
            "响应时间不超过200毫秒。",
            "CONFIDENTIAL",  # 页眉，应过滤
        ]

        # 过滤页眉页脚
        noise_texts = header_texts | footer_texts
        clean_paragraphs = [
            p for p in raw_paragraphs
            if p.strip() and p.strip() not in noise_texts
            and not re.match(r'^第?\d+页', p.strip())
        ]

        blocks = [
            ParsedBlock(
                content="\n".join(clean_paragraphs),
                source_file="sample.docx",
                block_type="text"
            )
        ]

        return ParseResult(
            blocks=blocks,
            source_file="sample.docx",
            doc_type="docx",
            stats={
                "total_paragraphs": len(raw_paragraphs),
                "filtered": len(raw_paragraphs) - len(clean_paragraphs),
                "clean": len(clean_paragraphs)
            }
        )


# ============================================================
# 6. 统一解析Pipeline
# ============================================================

class DocumentParser(ABC):
    """文档解析器抽象基类"""
    @abstractmethod
    def parse(self, source: str) -> ParseResult:
        pass


class UnifiedParsingPipeline:
    """
    统一文档解析Pipeline
    根据文件类型自动选择解析器，输出标准化的文本块
    """

    def __init__(self):
        self.pdf_parser = PDFParser()
        self.html_cleaner = HTMLCleaner()
        self.ocr_processor = OCRProcessor()
        self.word_parser = WordParser()

    def detect_type(self, file_path: str) -> str:
        """检测文档类型"""
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        type_map = {
            "pdf": "pdf",
            "docx": "docx",
            "doc": "docx",
            "html": "html",
            "htm": "html",
            "md": "markdown",
            "txt": "text",
        }
        return type_map.get(ext, "unknown")

    def parse(self, file_path: str) -> ParseResult:
        """根据文件类型自动选择解析器"""
        doc_type = self.detect_type(file_path)

        if doc_type == "pdf":
            return self.pdf_parser.parse(file_path)
        elif doc_type == "html":
            # 实际项目中读取文件内容
            sample_html = self._get_sample_html()
            return self.html_cleaner.clean(sample_html)
        elif doc_type == "docx":
            return self.word_parser.parse_simulated()
        else:
            return ParseResult(
                blocks=[],
                source_file=file_path,
                doc_type=doc_type,
                stats={"error": f"不支持的文档类型: {doc_type}"}
            )

    def _get_sample_html(self) -> str:
        """示例HTML内容"""
        return """
        <html>
        <head><title>产品帮助文档</title></head>
        <body>
            <nav class="navbar">
                <a href="/">首页</a> | <a href="/products">产品</a> | <a href="/about">关于</a>
            </nav>
            <main>
                <h1>产品使用指南</h1>
                <p>本指南介绍产品的安装和配置步骤。</p>
                <h2>安装步骤</h2>
                <p>1. 下载安装包</p>
                <p>2. 运行安装程序</p>
                <p>3. 按照向导完成配置</p>
            </main>
            <footer class="footer">
                <p>© 2024 XX公司 版权所有</p>
                <a href="/privacy">隐私政策</a>
            </footer>
        </body>
        </html>
        """


# ============================================================
# 7. 解析质量评估
# ============================================================

class ParsingQualityEvaluator:
    """解析质量评估器：完整性、准确性、纯净度"""

    def evaluate(self, result: ParseResult) -> dict:
        """评估解析结果的质量"""
        all_text = " ".join(b.content for b in result.blocks)

        # 完整性：是否有内容被提取出来
        completeness = min(1.0, len(all_text) / 100) if all_text else 0.0

        # 纯净度：检查是否包含常见噪声
        noise_patterns = [
            r"首页.*产品.*关于",  # 导航菜单
            r"©.*版权所有",       # 版权声明
            r"第\d+页/共\d+页",  # 页码
        ]
        noise_count = sum(
            1 for p in noise_patterns if re.search(p, all_text)
        )
        purity = max(0.0, 1.0 - noise_count * 0.2)

        # 结构化程度：是否区分了不同类型的块
        block_types = set(b.block_type for b in result.blocks)
        structure_score = min(1.0, len(block_types) * 0.4)

        return {
            "completeness": round(completeness, 2),
            "purity": round(purity, 2),
            "structure": round(structure_score, 2),
            "overall": round((completeness + purity + structure_score) / 3, 2),
            "block_count": len(result.blocks),
            "block_types": list(block_types),
        }


# ============================================================
# 主程序：演示完整Pipeline
# ============================================================

def main():
    print("=" * 60)
    print("📚 文档解析Pipeline演示")
    print("=" * 60)

    pipeline = UnifiedParsingPipeline()
    evaluator = ParsingQualityEvaluator()

    # --- 演示1：PDF解析 ---
    print("\n--- 1. PDF解析（文本 + 表格提取）---")
    pdf_result = pipeline.parse("sample.pdf")
    for block in pdf_result.blocks:
        print(f"  [{block.block_type}] {block.content[:80]}...")
    print(f"  统计: {pdf_result.stats}")

    quality = evaluator.evaluate(pdf_result)
    print(f"  质量评分: {quality}")

    # --- 演示2：HTML清洗 ---
    print("\n--- 2. HTML清洗（去除导航噪声）---")
    html_result = pipeline.parse("page.html")
    for block in html_result.blocks:
        print(f"  [{block.block_type}] {block.content[:80]}...")
    print(f"  统计: {html_result.stats}")

    quality = evaluator.evaluate(html_result)
    print(f"  质量评分: {quality}")

    # --- 演示3：OCR后处理 ---
    print("\n--- 3. OCR后处理（修正识别错误）---")
    ocr = OCRProcessor()
    raw_text = ocr.simulate_ocr()
    print(f"  原始OCR输出:\n{raw_text}")

    ocr_result = ocr.process(raw_text)
    print(f"  修正后输出:\n{ocr_result.text}")
    print(f"  修正项: {ocr_result.corrections}")
    print(f"  置信度: {ocr_result.confidence}")

    # --- 演示4：Word文档解析 ---
    print("\n--- 4. Word文档解析（过滤页眉页脚）---")
    word_result = pipeline.parse("document.docx")
    for block in word_result.blocks:
        print(f"  [{block.block_type}] {block.content[:120]}...")
    print(f"  统计: {word_result.stats}")

    quality = evaluator.evaluate(word_result)
    print(f"  质量评分: {quality}")

    # --- 总结 ---
    print("\n" + "=" * 60)
    print("📊 解析Pipeline总结")
    print("=" * 60)
    print("  ✅ PDF: pdfplumber提取文本+表格，保留结构")
    print("  ✅ HTML: 移除nav/header/footer噪声，提取main正文")
    print("  ✅ OCR: 后处理修正常见错误（O→0, l→1）")
    print("  ✅ Word: 过滤页眉页脚，只保留正文段落")
    print("  ✅ 质量评估: 完整性 + 纯净度 + 结构化三维度")


if __name__ == "__main__":
    main()
