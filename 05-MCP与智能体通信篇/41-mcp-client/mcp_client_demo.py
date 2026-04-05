"""MCP Client集成演示"""
class MockServer:
    def __init__(self, name, tools):
        self.name = name; self._tools = tools
    def list_tools(self): return self._tools
    def call(self, name, params):
        return {"result": f"[{self.name}] {name}执行成功", "params": params}

class MCPClient:
    def __init__(self): self.servers = {}; self.registry = {}
    def connect(self, server):
        self.servers[server.name] = server
        for t in server.list_tools():
            self.registry[t["name"]] = server.name
        print(f"  连接{server.name}: {[t['name'] for t in server.list_tools()]}")
    def call(self, tool, params):
        sn = self.registry.get(tool)
        if not sn: return {"error": "工具未注册"}
        return self.servers[sn].call(tool, params)
    def all_tools(self):
        return list(self.registry.keys())

def main():
    print("🧩 MCP Client演示\n")
    client = MCPClient()
    client.connect(MockServer("db", [{"name":"query_users","description":"查用户"}]))
    client.connect(MockServer("email", [{"name":"send_email","description":"发邮件"}]))
    print(f"\n所有工具: {client.all_tools()}")
    print(f"调用query_users: {client.call('query_users', {'id': 1})}")
    print(f"调用send_email: {client.call('send_email', {'to': 'a@b.com'})}")
    print(f"调用不存在的: {client.call('unknown', {})}")
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
