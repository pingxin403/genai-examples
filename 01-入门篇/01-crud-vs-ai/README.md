# 01-crud-vs-ai：CRUD确定性系统 vs AI概率性系统

> 对应文章：[《写CRUD和写AI应用，到底
《写CRUD和写AI应用，到底有什么不一样？》

## 这个示例解决什么问题？

演示一个最小 AI 问答流水线，重点不是“回答得多聪明”，而是“如何可控”：

- 质量阈值（置信度判断）
- 结构化输出校验
- 回退策略（模板/人工）
- 成本与可观测基础埋点（简化版）

## 目录结构

- `app.py`：最小可运行示例（Python）
- `sample_requests.json`：测试输入样例

## 运行方式

```bash
cd genai-examples/01-入门篇/01-crud-vs-ai
python app.py
```

## 你会看到什么？

程序会打印每个请求的：

- query
- confidence
- action（direct / cited / fallback）
- answer

用于直观理解“概率系统如何做运行时决策”。

## 关键工程点

1. **质量门控优先**：先定义可接受输出，再谈 Prompt。  
2. **流水线拆分**：检索、生成、校验、回退可定位。  
3. **兜底必备**：低置信度必须能优雅失败，而不是胡乱自信回答。  

## 后续可扩展

- 接入真实 LLM API
- 增加 JSON Schema 校验
- 增加 Token 统计与预算告警
- 增加评测集回归脚本