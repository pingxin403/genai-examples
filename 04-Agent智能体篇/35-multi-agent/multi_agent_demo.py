"""Multi-Agent协作演示"""

class Supervisor:
    def assign(self, query):
        tasks = []
        if "订单" in query: tasks.append(("order", "查询订单"))
        if "退款" in query: tasks.append(("finance", "计算退款"))
        if "通知" in query: tasks.append(("notify", "发送通知"))
        return tasks or [("general", query)]

class Specialist:
    def __init__(self, name):
        self.name = name
    def execute(self, task):
        return f"[{self.name}] 完成: {task}"

class Reviewer:
    def review(self, results):
        return {"approved": all(len(r) > 5 for r in results.values()),
                "count": len(results)}

def main():
    print("🧪 Multi-Agent协作演示\n")
    sup = Supervisor()
    agents = {"order": Specialist("订单专员"), "finance": Specialist("财务专员"),
              "notify": Specialist("通知专员"), "general": Specialist("通用专员")}
    rev = Reviewer()

    query = "帮我查订单并计算退款金额"
    tasks = sup.assign(query)
    print(f"主管分配: {tasks}")

    results = {}
    for domain, task in tasks:
        agent = agents.get(domain, agents["general"])
        results[domain] = agent.execute(task)
        print(f"  {results[domain]}")

    review = rev.review(results)
    print(f"质检: {'通过' if review['approved'] else '未通过'}")
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
