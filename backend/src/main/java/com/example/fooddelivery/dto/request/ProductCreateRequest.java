package com.example.fooddelivery.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class ProductCreateRequest {
    @NotBlank(message = "商品名称不能为空")
    private String name;
    private String image;
    @NotNull(message = "商品价格不能为空")
    @Positive(message = "商品价格必须大于0")
    private BigDecimal price;
    private BigDecimal originalPrice;
    private String description;
    private Integer stock = 0;
    private Long categoryId;
}