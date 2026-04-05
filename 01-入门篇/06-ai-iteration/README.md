# 06 - AI应用迭代Pipeline演示

> 对应文章：🔄《AI应用怎么迭代？和传统CI/CD完全不一样》

## 功能简述

演示AI应用的迭代闭环核心模块：Prompt版本管理、评估集驱动验证、用户反馈回流，展示如何构建一个可持续优化的AI迭代Pipeline。

## 运行环境

- Python 3.9+
- 无需额外依赖（使用模拟数据，不调用真实API）

## 运行方式

```bash
python ai_iteration_demo.py
```

## 代码结构

```
06-ai-iteration/
├── README.md                  # 本文件
└── ai_iteration_demo.py       # AI迭代Pipeline完整演示
```

## 预期输出

程序会模拟一次完整的AI迭代流程，展示：
1. Prompt版本注册与管理
2. 评估集验证（对比两个Prompt版本的通过率）
3. 用户反馈采集与满意率统计
4. 负面反馈回流为评估集候选

最终输出各版本的评估结果和反馈汇总。
