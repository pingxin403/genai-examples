# 14-streaming：流式响应SSE/WebSocket前后端联调实战

> 对应文章：[🧪《流式响应：SSE/WebSocket前后端联调实战》](../../../GenAI/02-Prompt工程篇/14-流式响应SSE-WebSocket前后端联调实战.md)

## 功能简述

演示LLM流式响应的完整实现，包括：
- SSE（Server-Sent Events）流式推送
- 逐chunk解析与拼接
- 用户中断（停止生成）处理
- 分阶段进度反馈
- 断线重连机制

## 运行环境

- Python 3.9+
- pip

## 依赖安装

```bash
pip install fastapi uvicorn openai
```

## 环境变量

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 运行命令

```bash
# 启动后端服务
uvicorn streaming_demo:app --reload --port 8000

# 运行演示脚本（无需API Key，使用模拟数据）
python streaming_demo.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `streaming_demo.py` | 完整演示：SSE服务端、流式解析、中断处理、进度反馈 |
| `README.md` | 本说明文件 |
