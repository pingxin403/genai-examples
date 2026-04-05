"""Agent记忆系统演示"""
import hashlib, math

class ShortTermMemory:
    def __init__(self, window=10):
        self.window = window
        self.history = []
        self.key_facts = []
    def add(self, role, content):
        self.history.append({"role": role, "content": content})
        if any(k in content for k in ["VIP", "年消费", "企业"]):
            self.key_facts.append(content[:80])
        if len(self.history) > self.window * 2:
            self.history = self.history[-self.window * 2:]
    def context(self):
        facts = "\n".join(f"[关键] {f}" for f in self.key_facts)
        recent = "\n".join(f"{m['role']}: {m['content'][:50]}" for m in self.history[-6:])
        return f"{facts}\n{recent}" if facts else recent

class LongTermMemory:
    def __init__(self):
        self.profiles = {}
    def update(self, uid, key, val):
        self.profiles.setdefault(uid, {})[key] = val
    def get(self, uid):
        return self.profiles.get(uid, {})

class SemanticMemory:
    def __init__(self):
        self.memories = []
    def store(self, content):
        emb = self._embed(content)
        self.memories.append((emb, content))
    def recall(self, query, top_k=3):
        q = self._embed(query)
        scored = [(self._cos(q, e), c) for e, c in self.memories]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]
    def _embed(self, t):
        h = hashlib.sha256(t.encode()).hexdigest()
        return [int(h[i:i+2],16)/255 for i in range(0,32,2)]
    def _cos(self, a, b):
        d = sum(x*y for x,y in zip(a,b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        return d/(na*nb) if na*nb>0 else 0

def main():
    print("=" * 50)
    print("🧩 Agent记忆系统演示")
    print("=" * 50)

    # 短时记忆
    print("\n--- 短时记忆 ---")
    stm = ShortTermMemory(window=5)
    stm.add("user", "我是VIP客户，年消费50万")
    stm.add("assistant", "好的，已记录您的VIP身份")
    for i in range(8):
        stm.add("user", f"第{i+3}轮普通对话")
        stm.add("assistant", f"回复第{i+3}轮")
    stm.add("user", "我能享受什么优惠？")
    print(f"  关键信息保留: {stm.key_facts}")
    print(f"  上下文:\n{stm.context()[:200]}...")

    # 长时记忆
    print("\n--- 长时记忆 ---")
    ltm = LongTermMemory()
    ltm.update("u001", "level", "VIP")
    ltm.update("u001", "annual_spend", "50万")
    print(f"  用户画像: {ltm.get('u001')}")

    # 语义记忆
    print("\n--- 语义记忆 ---")
    sem = SemanticMemory()
    sem.store("用户上次咨询了退货流程，最终成功退货")
    sem.store("用户偏好使用顺丰快递")
    sem.store("用户对产品A的评价很高")
    results = sem.recall("退货相关的历史", top_k=2)
    print(f"  召回: {results}")

    print("\n✅ 演示完成！")

if __name__ == "__main__":
    main()
