# 90 - AI Gateway对比演示

> 对应文章：[AI Gateway对比：LiteLLM/自研/云厂商怎么选？](../../../GenAI/11-生态与工具篇/90-AI-Gateway对比LiteLLM自研云厂商怎么选.md)

## 功能说明

演示三种AI Gateway方案的核心设计模式：
- LiteLLM风格：统一API代理 + 自动Fallback
- 自研Gateway：路由 + 限流 + 缓存 + 中间件
- 云厂商风格：托管服务 + 平台内模型
- 成本追踪与对比

## 运行环境

- Python 3.10+
- 无额外依赖（纯标准库实现）

## 运行方式

```bash
python gateway_comparison_demo.py
```

## 预期输出

- 三种Gateway方案的请求处理演示
- Fallback降级演示
- 成本统计与选型建议
