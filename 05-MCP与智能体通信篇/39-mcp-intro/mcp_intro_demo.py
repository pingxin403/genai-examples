"""MCP协议入门演示"""

class MCPServer:
    def __init__(self, name):
        self.name = name
        self.tools = {}
    def register(self, name, desc, handler):
        self.tools[name] = {"name": name, "description": desc, "handler": handler}
    def list_tools(self):
        return [{"name": t["name"], "description": t["description"]} for t in self.tools.values()]
    def call(self, name, params):
        tool = self.tools.get(name)
        if not tool: return {"error": f"工具{name}不存在"}
        return {"success": True, "result": tool["handler"](params)}

class MCPClient:
    def __init__(self):
        self.servers = {}
    def connect(self, server):
        self.servers[server.name] = server
        tools = server.list_tools()
        print(f"  连接 {server.name}，发现 {len(tools)} 个工具: {[t['name'] for t in tools]}")
    def call(self, server_name, tool_name, params):
        server = self.servers.get(server_name)
        if not server: return {"error": "Server未连接"}
        return server.call(tool_name, params)

def main():
    print("🔌 MCP协议演示\n")

    # 创建Server
    db_server = MCPServer("database")
    db_server.register("query_users", "查询用户信息", lambda p: {"users": [{"name": "张三", "age": 28}]})
    db_server.register("query_orders", "查询订单", lambda p: {"orders": [{"id": "ORD-001", "status": "已发货"}]})

    email_server = MCPServer("email")
    email_server.register("send_email", "发送邮件", lambda p: {"sent": True, "to": p.get("to", "")})

    # Client连接
    client = MCPClient()
    client.connect(db_server)
    client.connect(email_server)

    # 发现所有工具
    print(f"\n所有可用工具:")
    for name, server in client.servers.items():
        for tool in server.list_tools():
            print(f"  [{name}] {tool['name']}: {tool['description']}")

    # 调用工具
    print(f"\n调用工具:")
    r1 = client.call("database", "query_orders", {})
    print(f"  query_orders → {r1}")
    r2 = client.call("email", "send_email", {"to": "user@example.com"})
    print(f"  send_email → {r2}")

    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
