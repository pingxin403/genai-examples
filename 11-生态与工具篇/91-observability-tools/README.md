# 91 - 可观测性工具对比演示

> 对应文章：[可观测性工具：Datadog AI vs 自建OTel扩展](../../../GenAI/11-生态与工具篇/91-可观测性工具Datadog-AI-vs自建OTel扩展.md)

## 功能说明

演示两种AI可观测性方案的核心设计：
- Datadog AI Monitoring风格：自动采集LLM指标
- OpenTelemetry自建方案：自定义AI专属指标
- LLM Trace、Token追踪、成本归因
- AI健康度报告生成

## 运行环境

- Python 3.10+
- 无额外依赖（纯标准库实现）

## 运行方式

```bash
python observability_tools_demo.py
```

## 预期输出

- Datadog风格的Dashboard指标
- OTel风格的AI健康度报告
- 两种方案的对比总结
