package com.example.fooddelivery.dto.response;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class ProductResponse {
    private Long id;
    private String name;
    private String image;
    private BigDecimal price;
    private BigDecimal originalPrice;
    private String description;
    private Integer stock;
    private Integer sales;
    private Integer status;
    private Long categoryId;
    private String categoryName;
}