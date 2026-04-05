# 54 - LLM调用追踪演示

> 对应文章：[LLM调用追踪：把Prompt和Completion打进Trace](../../../GenAI/07-AI可观测性篇/54-LLM调用追踪把Prompt和Completion打进Trace.md)

## 功能说明

演示LLM调用的全链路追踪：
- LLM Span数据模型（语义载荷、Token、成本）
- 分层采样策略（异常100%、高成本100%、正常10%）
- Prompt摘要 + 哈希存储模式
- 成本自动计算与归因

## 运行环境

- Python 3.10+
- 无额外依赖（纯标准库实现）

## 运行方式

```bash
python llm_tracing_demo.py
```

## 预期输出

- 模拟多次LLM调用的Trace记录
- 展示Span详情（Prompt摘要、Token、成本）
- 按Trace ID查询调用链
