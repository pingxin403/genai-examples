# 89 - Embedding模型评测演示

> 对应文章：[Embedding模型评测：7款模型在5个领域的表现](../../../GenAI/11-生态与工具篇/89-Embedding模型评测7款模型在5个领域的表现.md)

## 功能说明

演示Embedding模型评测的核心流程：
- 7款主流Embedding模型的参数对比
- 5个垂直领域的评测数据集构建
- Hit Rate / MRR 指标计算
- 成本效益分析

## 运行环境

- Python 3.10+
- 无额外依赖（纯标准库实现）

## 运行方式

```bash
python embedding_benchmark_demo.py
```

## 预期输出

- 各模型在不同领域的Hit Rate对比
- 延迟与成本分析
- 选型建议
