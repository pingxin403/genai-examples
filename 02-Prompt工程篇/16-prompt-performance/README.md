# 📊 Prompt性能分析：Token计数、成本归因与预算预警

> 配套文章：[Prompt性能分析：一个Prompt吃掉多少Token？](../../../GenAI/02-Prompt工程篇/16-Prompt性能分析一个Prompt吃掉多少Token.md)

## 功能简述

本示例演示如何构建一个完整的Token性能分析系统，包括：

1. **Token精确计数** — 使用tiktoken计算Prompt的Token消耗
2. **多维度成本归因** — 按用户、场景、模型、Prompt版本拆分成本
3. **预算预警** — 实时检测日/月预算使用率，触发分级告警
4. **异常检测** — 发现单用户消耗异常或成本突增

## 运行环境

- Python 3.9+
- 无需API Key（纯本地计算演示）

## 依赖安装

```bash
pip install tiktoken
```

## 运行命令

```bash
python prompt_performance_demo.py
```

## 预期输出

```
=== Token计数演示 ===
短文本Token数: 11
长文本Token数: 约200+

=== 成本归因演示 ===
按场景汇总: {...}
按用户汇总: {...}
最贵的请求: [...]

=== 预算预警演示 ===
告警列表: [...]
```

## 核心文件

| 文件 | 说明 |
|------|------|
| `prompt_performance_demo.py` | 完整演示：Token计数 + 成本归因 + 预算预警 |
