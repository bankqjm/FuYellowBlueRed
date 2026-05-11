package com.example.fooddelivery.dto.response;

import lombok.Data;

@Data
public class LoginResponse {
    private String token;
    private String role;
    private Long userId;
    private String nickname;
    private String avatar;
}