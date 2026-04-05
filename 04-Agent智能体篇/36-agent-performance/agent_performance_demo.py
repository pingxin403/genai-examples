"""Agent性能优化演示"""
import time, concurrent.futures

def slow_step(name, duration=1):
    time.sleep(duration)
    return f"{name}完成"

def main():
    print("📊 Agent性能优化演示\n")

    # 串行执行
    start = time.time()
    r1 = slow_step("查数据库", 0.5)
    r2 = slow_step("清洗数据", 0.3)
    r3 = slow_step("计算指标", 0.4)
    serial = time.time() - start
    print(f"串行执行: {serial:.1f}秒")

    # 并行执行(查数据库和清洗数据可并行)
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        f1 = pool.submit(slow_step, "查数据库", 0.5)
        f2 = pool.submit(slow_step, "清洗数据", 0.3)
        f1.result(); f2.result()
    slow_step("计算指标", 0.4)
    parallel = time.time() - start
    print(f"并行执行: {parallel:.1f}秒")
    print(f"提升: {(1-parallel/serial)*100:.0f}%")

    # 上下文压缩
    long_text = "这是一段很长的中间结果" * 100
    compressed = long_text[:200] + f"...[压缩,原{len(long_text)}字]..." + long_text[-200:]
    print(f"\n上下文压缩: {len(long_text)} → {len(compressed)} 字符 ({len(compressed)/len(long_text)*100:.0f}%)")

    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
