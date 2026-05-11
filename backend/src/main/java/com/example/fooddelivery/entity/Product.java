package com.example.fooddelivery.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("products")
public class Product {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long shopId;
    private Long categoryId;
    private String name;
    private String image;
    private BigDecimal price;
    private BigDecimal originalPrice;
    private String description;
    private Integer stock;
    private Integer sales;
    private Integer status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}