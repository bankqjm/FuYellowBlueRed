package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.config.JwtConfig;
import com.example.fooddelivery.dto.request.LoginRequest;
import com.example.fooddelivery.dto.request.RegisterRequest;
import com.example.fooddelivery.dto.response.LoginResponse;
import com.example.fooddelivery.entity.User;
import com.example.fooddelivery.entity.Wallet;
import com.example.fooddelivery.mapper.UserMapper;
import com.example.fooddelivery.mapper.WalletMapper;
import com.example.fooddelivery.service.UserService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

@Service
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final WalletMapper walletMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtConfig jwtConfig;

    public UserServiceImpl(UserMapper userMapper, WalletMapper walletMapper, 
                          PasswordEncoder passwordEncoder, JwtConfig jwtConfig) {
        this.userMapper = userMapper;
        this.walletMapper = walletMapper;
        this.passwordEncoder = passwordEncoder;
        this.jwtConfig = jwtConfig;
    }

    @Override
    public LoginResponse login(LoginRequest request) {
        User user = userMapper.findByPhone(request.getPhone());
        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new RuntimeException("手机号或密码错误");
        }
        if (user.getStatus() != 1) {
            throw new RuntimeException("账号已禁用");
        }
        String token = jwtConfig.generateToken(user.getId(), user.getRole());
        LoginResponse response = new LoginResponse();
        response.setToken(token);
        response.setRole(user.getRole());
        response.setUserId(user.getId());
        response.setNickname(user.getNickname());
        response.setAvatar(user.getAvatar());
        return response;
    }

    @Override
    @Transactional
    public User register(RegisterRequest request) {
        if (userMapper.findByPhone(request.getPhone()) != null) {
            throw new RuntimeException("手机号已被注册");
        }
        User user = new User();
        user.setPhone(request.getPhone());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setNickname(request.getNickname());
        user.setRole(request.getRole());
        user.setStatus(1);
        userMapper.insert(user);

        Wallet wallet = new Wallet();
        wallet.setUserId(user.getId());
        wallet.setBalance(BigDecimal.ZERO);
        wallet.setFrozenBalance(BigDecimal.ZERO);
        walletMapper.insert(wallet);

        return user;
    }

    @Override
    public User findById(Long id) {
        return userMapper.selectById(id);
    }

    @Override
    public User findByPhone(String phone) {
        return userMapper.findByPhone(phone);
    }

    @Override
    public void update(User user) {
        userMapper.updateById(user);
    }
}