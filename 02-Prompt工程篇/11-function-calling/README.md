# 🔁 函数调用（Function Calling）工程化落地 — 代码示例

> 配套文章：《函数调用（Function Calling）的工程化落地》

## 功能简述

演示Function Calling从Schema设计到超时熔断的全流程工程化实践：
1. **工具Schema设计**：规范的工具定义与参数约束
2. **参数校验**：对模型生成的参数做严格校验
3. **错误处理**：带重试限制的工具调用执行器
4. **超时熔断**：CircuitBreaker模式防止级联故障
5. **完整编排**：端到端的Function Calling流程演示

## 运行环境

- Python 3.9+
- 无需额外依赖（纯演示逻辑，不调用真实API）

## 运行方式

```bash
cd genai-examples/02-Prompt工程篇/11-function-calling/
python function_calling_demo.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `function_calling_demo.py` | Function Calling工程化全流程演示，含Schema设计、参数校验、错误处理、熔断器 |
| `README.md` | 本文件 |

## 输出示例

运行后会依次展示：工具Schema定义、参数校验（正确/错误用例）、带重试的工具调用、熔断器状态变化、端到端流程演示。
