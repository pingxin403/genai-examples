/**
 * CRUD应用示例：传统用户查询服务
 *
 * 演示确定性系统的典型特征：
 * - 同输入同输出
 * - 错误是显性的（异常/状态码）
 * - 测试用精确断言
 *
 * 对应文章：《写CRUD和写AI应用，到底有什么不一样？》
 */

import java.util.*;

public class crud_example {

    // ========== 数据层 ==========
    static Map<Long, Map<String, Object>> userDB = new HashMap<>();

    static {
        userDB.put(1L, Map.of("id", 1L, "name", "张三", "email", "zhangsan@example.com"));
        userDB.put(2L, Map.of("id", 2L, "name", "李四", "email", "lisi@example.com"));
    }

    // ========== 确定性服务层 ==========

    /**
     * 根据ID查询用户 —— 确定性操作
     * 输入1，永远返回张三；输入999，永远抛异常
     */
    public static Map<String, Object> getUserById(Long id) {
        if (id == null) {
            throw new IllegalArgumentException("用户ID不能为空");
        }
        Map<String, Object> user = userDB.get(id);
        if (user == null) {
            throw new RuntimeException("用户不存在: " + id);
        }
        return user;
    }

    /**
     * 创建用户 —— 确定性操作
     * 同样的输入，结果可预测（成功或因重复而失败）
     */
    public static Map<String, Object> createUser(Long id, String name, String email) {
        if (userDB.containsKey(id)) {
            throw new RuntimeException("用户已存在: " + id);
        }
        Map<String, Object> user = Map.of("id", id, "name", name, "email", email);
        userDB.put(id, user);
        return user;
    }

    // ========== 确定性测试 ==========

    /**
     * CRUD测试：精确断言，100%可重复
     */
    public static void testGetUserById() {
        Map<String, Object> user = getUserById(1L);
        assert "张三".equals(user.get("name")) : "期望张三，实际: " + user.get("name");
        assert "zhangsan@example.com".equals(user.get("email"));
        System.out.println("✅ testGetUserById 通过 —— 同输入永远同输出");
    }

    public static void testUserNotFound() {
        try {
            getUserById(999L);
            assert false : "应该抛出异常";
        } catch (RuntimeException e) {
            assert e.getMessage().contains("用户不存在");
            System.out.println("✅ testUserNotFound 通过 —— 错误是显性的、可预测的");
        }
    }

    // ========== 运行入口 ==========

    public static void main(String[] args) {
        System.out.println("=== CRUD应用示例：确定性系统 ===\n");

        // 演示确定性查询
        System.out.println("查询用户1: " + getUserById(1L));
        System.out.println("查询用户2: " + getUserById(2L));
        System.out.println("再次查询用户1: " + getUserById(1L));
        System.out.println("\n→ 同一个ID，无论调多少次，结果完全一致\n");

        // 运行测试
        testGetUserById();
        testUserNotFound();

        System.out.println("\n=== CRUD核心特征 ===");
        System.out.println("1. 确定性：同输入 → 同输出");
        System.out.println("2. 显性错误：异常/状态码明确告诉你哪里出了问题");
        System.out.println("3. 精确测试：assertEquals 就够了");
        System.out.println("4. 成本可预测：和请求量线性相关");
    }
}
