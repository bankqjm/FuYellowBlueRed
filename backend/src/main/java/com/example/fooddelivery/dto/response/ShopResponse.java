package com.example.fooddelivery.dto.response;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class ShopResponse {
    private Long id;
    private String name;
    private String logo;
    private String address;
    private BigDecimal latitude;
    private BigDecimal longitude;
    private String businessHours;
    private String notice;
    private BigDecimal rating;
    private Integer status;
    private LocalDateTime createdAt;
}