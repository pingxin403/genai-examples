# 🧱 RAG进化史：从Naive到Modular

> 配套文章：《RAG进化史：从Naive到Modular，你的架构在第几层？》

## 功能简述

本示例演示RAG架构的三代演进，包含：

1. **朴素RAG（Naive RAG）**：固定切块 → 向量检索 → 直接生成
2. **高级RAG（Advanced RAG）**：查询改写 → 混合检索 → Rerank精排 → 生成
3. **模块化RAG（Modular RAG）**：意图路由 → 可编排Pipeline → 质量反馈

每一代都用模拟数据展示核心流程和效果差异。

## 运行环境

- Python 3.10+
- 无需外部API Key（使用模拟LLM和向量库）

## 依赖安装

```bash
pip install numpy
```

## 运行命令

```bash
python rag_evolution_demo.py
```

## 预期输出

程序会依次运行三代RAG架构，展示：
- 各代架构的检索流程
- 召回结果对比
- 质量评分和延迟对比

## 目录结构

```
17-rag-evolution/
├── README.md                  # 本文件
└── rag_evolution_demo.py      # 三代RAG演示代码
```
