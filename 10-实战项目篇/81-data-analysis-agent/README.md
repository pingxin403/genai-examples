# 81 - 数据分析Agent演示

> 对应文章：[数据分析Agent：NL2SQL+工具调用+可视化](../../../GenAI/10-实战项目篇/81-数据分析Agent-NL2SQL加工具调用加可视化.md)

## 功能说明

演示自然语言数据分析Agent的核心能力：
- Schema管理与上下文构建
- NL2SQL生成（模拟）
- SQL安全检查（禁止写操作/强制LIMIT）
- 查询执行与结果解释
- 可视化图表推荐

## 运行环境

- Python 3.10+
- 无额外依赖（纯标准库实现，使用SQLite内存数据库）

## 运行方式

```bash
python data_analysis_agent_demo.py
```

## 预期输出

- Schema注册与上下文构建
- SQL安全检查结果
- 查询执行与结果解释
- 可视化推荐
