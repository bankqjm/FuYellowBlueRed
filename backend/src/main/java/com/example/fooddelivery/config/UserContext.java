package com.example.fooddelivery.config;

public class UserContext {
    private static final ThreadLocal<Long> userId = new ThreadLocal<>();
    private static final ThreadLocal<String> role = new ThreadLocal<>();

    public static void setUserId(Long id) {
        userId.set(id);
    }

    public static Long getUserId() {
        return userId.get();
    }

    public static void setRole(String r) {
        role.set(r);
    }

    public static String getRole() {
        return role.get();
    }

    public static void clear() {
        userId.remove();
        role.remove();
    }
}