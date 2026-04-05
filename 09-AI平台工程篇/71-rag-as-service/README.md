# 71 - 知识库即服务演示

> 对应文章：[知识库即服务：为10个业务线提供统一RAG能力](../../../GenAI/09-AI平台工程篇/71-知识库即服务为10个业务线提供统一RAG能力.md)

## 功能说明

演示RAG-as-a-Service平台的核心能力：
- 多租户注册与管理（Free/Standard/Premium）
- 文档摄入Pipeline（分块+Embedding）
- 租户隔离检索
- 配额控制与统计

## 运行环境

- Python 3.10+
- 无额外依赖（纯标准库实现）

## 运行方式

```bash
python rag_as_service_demo.py
```

## 预期输出

- 多租户注册
- 文档摄入与分块
- 租户隔离检索演示
- 配额限制演示
- 租户统计信息
