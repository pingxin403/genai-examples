# 92 - AI安全工具评测演示

> 对应文章：[AI安全工具：Lakera/Guardrails/NeMo Guardrails评测](../../../GenAI/11-生态与工具篇/92-AI安全工具Lakera-Guardrails-NeMo评测.md)

## 功能说明

演示三大AI安全工具的核心防护模式：
- Lakera Guard风格：输入威胁检测 + PII脱敏
- Guardrails AI风格：输出验证与自动修复
- NeMo Guardrails风格：对话流程控制与话题约束
- 分层防御Pipeline演示

## 运行环境

- Python 3.10+
- 无额外依赖（纯标准库实现）

## 运行方式

```bash
python security_tools_demo.py
```

## 预期输出

- 各种攻击输入的检测结果
- 输出验证与自动修复演示
- 话题限制与对话控制演示
- 分层防御效果总结
