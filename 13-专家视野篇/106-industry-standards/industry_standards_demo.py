"""行业标准演示：多标准适配、标准追踪"""


class StandardsAdapter:
    def to_openai(self, tool: dict) -> dict:
        return {"type": "function", "function": {
            "name": tool["name"], "description": tool.get("description", ""),
            "parameters": tool.get("parameters", {})}}

    def to_mcp(self, tool: dict) -> dict:
        return {"name": tool["name"], "description": tool.get("description", ""),
                "inputSchema": tool.get("parameters", {})}

    def convert(self, tool: dict, target: str) -> dict:
        return {"openai": self.to_openai, "mcp": self.to_mcp}[target](tool)


class StandardsTracker:
    def __init__(self):
        self.standards: dict[str, dict] = {}

    def register(self, name: str, version: str, status: str, adoption: float):
        self.standards[name] = {"version": version, "status": status, "adoption": adoption}

    def recommend(self) -> list[dict]:
        recs = []
        for name, info in self.standards.items():
            if info["adoption"] > 0.3 and info["status"] == "stable":
                recs.append({"standard": name, "priority": "adopt"})
            elif info["status"] == "emerging":
                recs.append({"standard": name, "priority": "watch"})
        return recs


def main():
    print("=" * 60)
    print("行业标准演示")
    print("=" * 60)

    print("\n--- 多标准适配 ---")
    adapter = StandardsAdapter()
    tool = {"name": "search_docs", "description": "搜索文档",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}

    for fmt in ["openai", "mcp"]:
        result = adapter.convert(tool, fmt)
        print(f"  {fmt:<8} → {result}")

    print("\n--- 标准演进追踪 ---")
    tracker = StandardsTracker()
    tracker.register("OpenAI API", "v1", "stable", 0.85)
    tracker.register("MCP", "v1.0", "emerging", 0.25)
    tracker.register("EU AI Act", "2024", "stable", 0.40)

    for rec in tracker.recommend():
        icon = "✅" if rec["priority"] == "adopt" else "👀"
        print(f"  {icon} {rec['standard']} → {rec['priority']}")

    print(f"\n{'=' * 60}")
    print("核心: 抽象层隔离标准差异, 关注但不过早押注")
    print("=" * 60)


if __name__ == "__main__":
    main()
