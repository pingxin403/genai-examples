"""MCP vs 传统API对比演示"""
def main():
    print("🆚 MCP vs 传统API对比\n")
    comparison = [
        ("契约方式", "静态(OpenAPI)", "动态(运行时发现)"),
        ("调用方", "开发者写代码", "AI Agent自动"),
        ("新增工具", "改代码+部署", "注册即可用"),
        ("适用场景", "系统间集成", "AI工具调用"),
    ]
    print(f"{'维度':<12} {'传统API':<20} {'MCP':<20}")
    print("-" * 52)
    for dim, api, mcp in comparison:
        print(f"{dim:<12} {api:<20} {mcp:<20}")
    
    print("\n选型建议:")
    print("  • 系统间固定集成 → 传统API")
    print("  • AI Agent动态调用 → MCP")
    print("  • 推荐混合方案：核心用API，AI层用MCP包装")
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
