# 📚 非结构化数据"洗"成向量：文档解析示例

> 配套文章：[《非结构化数据"洗"成向量：文档解析的5个坑》](../../../GenAI/03-RAG深度篇/18-非结构化数据洗成向量文档解析的5个坑.md)

## 功能简述

演示RAG系统中文档解析Pipeline的核心技术：

- **PDF解析**：使用pdfplumber提取文本和表格，保留表格结构
- **HTML清洗**：移除导航、页脚等噪声标签，提取正文内容
- **OCR后处理**：模拟扫描件文字识别及常见错误修正
- **表格转文本**：将二维表格转为可检索的结构化文本
- **解析质量评估**：完整性、准确性、纯净度三维度评估

## 运行环境

- Python 3.10+

## 依赖安装

```bash
pip install pdfplumber beautifulsoup4 python-docx
```

> OCR功能需额外安装 `pytesseract` 或 `paddleocr`，本示例使用模拟数据演示流程。

## 运行命令

```bash
python doc_parsing_demo.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `doc_parsing_demo.py` | 文档解析Pipeline完整示例 |
| `README.md` | 本说明文件 |
