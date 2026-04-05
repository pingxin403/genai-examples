"""MCP Server实现演示"""
import time

class MCPServer:
    def __init__(self, name):
        self.name = name; self.tools = {}; self.tokens = set(); self.calls = {}
    def register(self, name, desc, handler, auth=False, limit=60):
        self.tools[name] = {"desc": desc, "handler": handler, "auth": auth, "limit": limit}
    def add_token(self, t): self.tokens.add(t)
    def list_tools(self):
        return [{"name": n, "description": t["desc"]} for n, t in self.tools.items()]
    def call(self, name, params, token=None):
        tool = self.tools.get(name)
        if not tool: return {"error": "工具不存在"}
        if tool["auth"] and token not in self.tokens: return {"error": "认证失败"}
        now = time.time()
        times = [t for t in self.calls.get(name, []) if now-t<60]
        if len(times) >= tool["limit"]: return {"error": "频率超限"}
        times.append(now); self.calls[name] = times
        return {"result": tool["handler"](params)}

def main():
    print("🏗️ MCP Server演示\n")
    server = MCPServer("inventory")
    server.register("check_stock", "查询库存", lambda p: {"product": p.get("id","?"), "stock": 42})
    server.register("update_stock", "更新库存(需认证)", lambda p: {"updated": True}, auth=True, limit=10)
    server.add_token("secret-token-123")

    print("工具列表:", server.list_tools())
    print("\n查询库存:", server.call("check_stock", {"id": "SKU-001"}))
    print("更新库存(无token):", server.call("update_stock", {"id": "SKU-001", "delta": -1}))
    print("更新库存(有token):", server.call("update_stock", {"id": "SKU-001", "delta": -1}, "secret-token-123"))
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
