"""MCP安全模型演示"""
class SecureMCPClient:
    def __init__(self): self.perms = {}; self.logs = []
    def set_perms(self, uid, tools): self.perms[uid] = set(tools)
    def call(self, uid, tool, params):
        allowed = self.perms.get(uid, set())
        if tool not in allowed:
            self.logs.append(f"DENIED: {uid}→{tool}")
            return {"error": f"{uid}无权调用{tool}"}
        self.logs.append(f"OK: {uid}→{tool}")
        return {"result": f"{tool}执行成功", "caller": uid}

def main():
    print("🔒 MCP安全模型演示\n")
    client = SecureMCPClient()
    client.set_perms("user_001", ["query_order", "query_logistics"])
    client.set_perms("admin_001", ["query_order", "query_logistics", "cancel_order", "delete_user"])

    tests = [
        ("user_001", "query_order", "普通用户查询(应通过)"),
        ("user_001", "cancel_order", "普通用户取消(应拒绝)"),
        ("admin_001", "cancel_order", "管理员取消(应通过)"),
    ]
    for uid, tool, desc in tests:
        r = client.call(uid, tool, {})
        status = "✅" if "result" in r else "🚫"
        print(f"  {status} {desc}: {r}")

    print(f"\n审计日志: {client.logs}")
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
