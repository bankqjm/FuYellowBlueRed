package com.example.fooddelivery.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class ShopCreateRequest {
    @NotBlank(message = "店铺名称不能为空")
    private String name;
    private String logo;
    @NotBlank(message = "店铺地址不能为空")
    private String address;
    private BigDecimal latitude;
    private BigDecimal longitude;
    private String businessHours;
    private String notice;
}