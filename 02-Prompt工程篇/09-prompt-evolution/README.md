# 🧩 Prompt工程进化的四个阶段 — 代码示例

> 配套文章：《从零样本到思维链：Prompt工程进化的四个阶段》

## 功能简述

演示Prompt工程的四个演进阶段：
1. **零样本（Zero-Shot）**：直接描述任务，不提供示例
2. **少样本（Few-Shot）**：通过示例引导模型输出格式和风格
3. **思维链（Chain-of-Thought）**：引导模型逐步推理
4. **自洽性（Self-Consistency）**：多次采样+投票，提高可靠性

## 运行环境

- Python 3.9+
- 无需额外依赖（纯演示逻辑，不调用真实API）

## 运行方式

```bash
cd genai-examples/02-Prompt工程篇/09-prompt-evolution/
python prompt_evolution_demo.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `prompt_evolution_demo.py` | 四个阶段的完整演示，含Prompt构建、模拟调用、效果对比 |
| `README.md` | 本文件 |

## 输出示例

运行后会依次展示四个阶段的Prompt构建方式、模拟输出和效果对比表格。
