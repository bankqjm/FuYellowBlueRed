package com.example.fooddelivery.service;

import com.example.fooddelivery.dto.request.LoginRequest;
import com.example.fooddelivery.dto.request.RegisterRequest;
import com.example.fooddelivery.dto.response.LoginResponse;
import com.example.fooddelivery.entity.User;

public interface UserService {
    LoginResponse login(LoginRequest request);
    User register(RegisterRequest request);
    User findById(Long id);
    User findByPhone(String phone);
    void update(User user);
}