"""
流式响应SSE/WebSocket前后端联调实战 - 演示代码
对应文章：《流式响应：SSE/WebSocket前后端联调实战》

演示内容：
1. SSE流式推送服务端实现
2. 流式chunk解析与拼接
3. 用户中断处理
4. 分阶段进度反馈
5. 断线重连机制

运行方式：
  python streaming_demo.py          # 运行全部演示（使用模拟数据）
  uvicorn streaming_demo:app --reload  # 启动FastAPI服务（需要OPENAI_API_KEY）
"""

import json
import time
import asyncio
import threading
from typing import Generator, AsyncGenerator, Optional, Callable


# ============================================================
# 第一部分：SSE数据格式与解析
# ============================================================

class SSEFormatter:
    """SSE数据格式化工具"""

    @staticmethod
    def format_event(data: str, event_type: str = None) -> str:
        """将数据格式化为SSE事件格式"""
        lines = []
        if event_type:
            lines.append(f"event: {event_type}")
        lines.append(f"data: {data}")
        lines.append("")  # SSE要求空行分隔
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def format_done() -> str:
        return "data: [DONE]\n\n"


class SSEParser:
    """SSE流式数据解析器 - 处理不完整chunk的核心逻辑"""

    def __init__(self):
        self.buffer = ""

    def feed(self, raw_text: str) -> list:
        """
        喂入原始文本，返回解析出的完整事件列表。
        关键：用buffer处理TCP分包导致的不完整行。
        """
        self.buffer += raw_text
        events = []

        lines = self.buffer.split("\n")
        self.buffer = lines.pop()  # 最后一个可能不完整，留到下次

        for line in lines:
            line = line.strip()
            if line.startswith("data: "):
                payload = line[6:]
                if payload == "[DONE]":
                    events.append({"type": "done"})
                else:
                    try:
                        parsed = json.loads(payload)
                        events.append(parsed)
                    except json.JSONDecodeError:
                        pass  # 跳过解析失败的行

        return events


# ============================================================
# 第二部分：模拟LLM流式输出
# ============================================================

def simulate_llm_stream(question: str) -> Generator[str, None, None]:
    """模拟LLM逐token生成（不需要真实API Key）"""
    answer = f"关于「{question}」，我来详细解答。流式响应的核心价值在于降低用户感知延迟。"

    for char in answer:
        time.sleep(0.05)  # 模拟token生成延迟
        yield char


async def async_simulate_llm_stream(question: str) -> AsyncGenerator[str, None]:
    """异步版本的模拟LLM流式输出"""
    answer = f"关于「{question}」，我来详细解答。流式响应让用户从干等变成边看边等，体验提升显著。"

    for char in answer:
        await asyncio.sleep(0.03)
        yield char


# ============================================================
# 第三部分：SSE流式服务端（FastAPI）
# ============================================================

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import StreamingResponse, HTMLResponse

    app = FastAPI(title="流式响应演示")

    async def stream_chat_sse(question: str, request: Request):
        """带进度反馈和中断检测的SSE流式响应"""
        formatter = SSEFormatter()

        # 阶段1：思考中
        yield formatter.format_event(
            json.dumps({"type": "status", "content": "正在理解您的问题..."}, ensure_ascii=False)
        )
        await asyncio.sleep(0.3)

        # 阶段2：检索（模拟RAG场景）
        yield formatter.format_event(
            json.dumps({"type": "status", "content": "正在检索相关知识..."}, ensure_ascii=False)
        )
        await asyncio.sleep(0.3)

        # 阶段3：逐token输出
        async for token in async_simulate_llm_stream(question):
            if await request.is_disconnected():
                print("客户端已断开，停止生成")
                return
            yield formatter.format_event(
                json.dumps({"type": "content", "content": token}, ensure_ascii=False)
            )

        # 阶段4：完成
        yield formatter.format_done()

    @app.post("/api/chat")
    async def chat_endpoint(request: Request):
        body = await request.json()
        question = body.get("question", "你好")

        return StreamingResponse(
            stream_chat_sse(question, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/")
    async def index():
        """简易前端页面"""
        html = """
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"><title>流式响应演示</title></head>
        <body style="font-family:sans-serif;max-width:600px;margin:40px auto;">
        <h2>🧪 流式响应演示</h2>
        <input id="q" placeholder="输入问题..." style="width:70%;padding:8px;">
        <button onclick="send()">发送</button>
        <button onclick="stop()" id="stopBtn" disabled>停止生成</button>
        <div id="status" style="color:gray;margin:10px 0;"></div>
        <div id="output" style="white-space:pre-wrap;border:1px solid #ddd;padding:12px;min-height:100px;"></div>
        <script>
        let controller;
        async function send() {
          const q = document.getElementById('q').value;
          const output = document.getElementById('output');
          const status = document.getElementById('status');
          output.textContent = '';
          status.textContent = '';
          document.getElementById('stopBtn').disabled = false;
          controller = new AbortController();
          try {
            const res = await fetch('/api/chat', {
              method:'POST', headers:{'Content-Type':'application/json'},
              body: JSON.stringify({question:q}), signal: controller.signal
            });
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            while(true) {
              const {done, value} = await reader.read();
              if(done) break;
              buffer += decoder.decode(value, {stream:true});
              const lines = buffer.split('\\n');
              buffer = lines.pop();
              for(const line of lines) {
                if(line.startsWith('data: ')) {
                  const d = line.slice(6);
                  if(d==='[DONE]'){status.textContent='✅ 生成完成';break;}
                  try{
                    const p=JSON.parse(d);
                    if(p.type==='status') status.textContent=p.content;
                    else if(p.type==='content') output.textContent+=p.content;
                  }catch(e){}
                }
              }
            }
          } catch(e) {
            if(e.name==='AbortError') status.textContent='⏹ 已停止生成';
            else status.textContent='❌ 错误: '+e.message;
          }
          document.getElementById('stopBtn').disabled = true;
        }
        function stop() { if(controller) controller.abort(); }
        </script></body></html>
        """
        return HTMLResponse(html)

except ImportError:
    app = None  # FastAPI未安装时跳过


# ============================================================
# 第四部分：中断处理演示
# ============================================================

class InterruptibleStream:
    """可中断的流式生成器"""

    def __init__(self):
        self._cancelled = False
        self.collected_text = ""

    def cancel(self):
        self._cancelled = True

    def stream(self, question: str) -> Generator[str, None, None]:
        for token in simulate_llm_stream(question):
            if self._cancelled:
                print(f"  [中断] 已生成 {len(self.collected_text)} 字符后停止")
                return
            self.collected_text += token
            yield token


# ============================================================
# 第五部分：断线重连机制
# ============================================================

class ResilientStreamClient:
    """带断线重连的流式客户端"""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.received_content = ""
        self.retry_count = 0

    def connect_and_stream(
        self,
        question: str,
        on_chunk: Callable[[str], None],
        simulate_disconnect_at: Optional[int] = None,
    ):
        """
        连接并接收流式数据，支持断线重连。
        simulate_disconnect_at: 模拟在第N个字符时断线
        """
        char_count = 0

        while self.retry_count <= self.max_retries:
            try:
                for token in simulate_llm_stream(question):
                    char_count += 1
                    if simulate_disconnect_at and char_count == simulate_disconnect_at:
                        raise ConnectionError("模拟网络断开")

                    self.received_content += token
                    on_chunk(token)
                    self.retry_count = 0

                return  # 正常完成

            except ConnectionError as e:
                self.retry_count += 1
                if self.retry_count <= self.max_retries:
                    wait = self.retry_count
                    print(f"\n  [重连] 连接断开，{wait}秒后第{self.retry_count}次重试...")
                    time.sleep(wait)
                else:
                    print(f"\n  [失败] 超过最大重试次数({self.max_retries})，放弃连接")
                    raise


# ============================================================
# 演示入口
# ============================================================

def demo_sse_format():
    """演示1：SSE数据格式化与解析"""
    print("=" * 60)
    print("演示1：SSE数据格式化与解析")
    print("=" * 60)

    formatter = SSEFormatter()

    # 格式化
    raw_sse = ""
    raw_sse += formatter.format_event('{"type":"status","content":"思考中..."}')
    raw_sse += formatter.format_event('{"type":"content","content":"你"}')
    raw_sse += formatter.format_event('{"type":"content","content":"好"}')
    raw_sse += formatter.format_done()

    print("SSE原始数据：")
    print(raw_sse)

    # 解析
    parser = SSEParser()
    events = parser.feed(raw_sse)
    print("解析结果：")
    for event in events:
        print(f"  {event}")
    print()


def demo_streaming_output():
    """演示2：模拟流式输出"""
    print("=" * 60)
    print("演示2：模拟LLM流式输出")
    print("=" * 60)

    print("问题：什么是SSE？")
    print("回答：", end="", flush=True)

    full_text = ""
    for token in simulate_llm_stream("什么是SSE"):
        print(token, end="", flush=True)
        full_text += token

    print(f"\n\n总共生成 {len(full_text)} 个字符")
    print()


def demo_interrupt():
    """演示3：中断处理"""
    print("=" * 60)
    print("演示3：用户中断（停止生成）")
    print("=" * 60)

    stream = InterruptibleStream()

    print("开始生成，3秒后模拟用户点击'停止生成'...")
    print("回答：", end="", flush=True)

    # 3秒后触发中断
    timer = threading.Timer(0.5, stream.cancel)
    timer.start()

    for token in stream.stream("请详细解释流式响应的原理"):
        print(token, end="", flush=True)

    print(f"\n已收集文本：{stream.collected_text}")
    print()


def demo_reconnect():
    """演示4：断线重连"""
    print("=" * 60)
    print("演示4：断线重连机制")
    print("=" * 60)

    client = ResilientStreamClient(max_retries=3)

    print("模拟在第5个字符时网络断开...")
    print("回答：", end="", flush=True)

    try:
        client.connect_and_stream(
            "SSE的优势是什么",
            on_chunk=lambda t: print(t, end="", flush=True),
            simulate_disconnect_at=5,
        )
    except ConnectionError:
        print("\n连接最终失败")

    print(f"\n已接收内容：{client.received_content}")
    print()


def demo_progress_feedback():
    """演示5：分阶段进度反馈"""
    print("=" * 60)
    print("演示5：分阶段进度反馈")
    print("=" * 60)

    stages = [
        ("status", "正在理解您的问题..."),
        ("status", "正在检索相关知识..."),
        ("status", "正在生成回答..."),
    ]

    for stage_type, message in stages:
        print(f"  [{stage_type}] {message}")
        time.sleep(0.3)

    print("  [content] ", end="")
    for token in simulate_llm_stream("流式响应的优势"):
        print(token, end="", flush=True)

    print("\n  [done] 生成完成")
    print()


if __name__ == "__main__":
    print("\n🧪 流式响应SSE/WebSocket前后端联调实战 - 演示\n")

    demo_sse_format()
    demo_streaming_output()
    demo_interrupt()
    demo_reconnect()
    demo_progress_feedback()

    print("=" * 60)
    print("全部演示完成！")
    print()
    if app:
        print("启动Web服务：uvicorn streaming_demo:app --reload")
        print("访问 http://localhost:8000 体验交互式演示")
    else:
        print("提示：安装 fastapi uvicorn 可体验Web交互式演示")
