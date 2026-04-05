# 🧠 输出结构化控制的3层防线 — 代码示例

> 配套文章：《别让AI乱说话！输出结构化控制的3层防线》

## 功能简述

演示AI输出结构化控制的三层防线完整实现：
1. **第1层：JSON模式** — 强制模型输出合法JSON
2. **第2层：Pydantic校验** — 校验字段类型、格式、必填项
3. **第3层：业务规则验证** — 校验业务逻辑合理性
4. **重试修复机制** — 校验失败时带错误反馈重试
5. **完整Pipeline** — 三层防线 + 重试的端到端流程

## 运行环境

- Python 3.9+
- 无需额外依赖（纯演示逻辑，不调用真实API）

## 运行方式

```bash
cd genai-examples/02-Prompt工程篇/12-structured-output/
python structured_output_demo.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `structured_output_demo.py` | 三层防线完整演示，含JSON解析、Pydantic校验、业务规则、重试修复 |
| `README.md` | 本文件 |

## 输出示例

运行后会依次展示：JSON模式解析、Pydantic结构校验（正确/错误用例）、业务规则验证、重试修复流程、端到端Pipeline演示。
