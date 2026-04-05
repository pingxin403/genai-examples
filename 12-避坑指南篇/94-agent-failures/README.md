# 94 - Agent失控实录演示

> 对应文章：[Agent失控实录：死循环、工具滥用、天价账单](../../../GenAI/12-避坑指南篇/94-Agent失控实录死循环工具滥用天价账单.md)

## 功能说明

演示Agent失控的三大模式及防护机制：
- 熔断器：检测死循环并强制终止
- 工具权限管理：控制Agent能调用哪些工具
- 成本监控：实时Token消耗追踪
- 分层防御Pipeline

## 运行环境

- Python 3.10+
- 无额外依赖

## 运行方式

```bash
python agent_failures_demo.py
```
