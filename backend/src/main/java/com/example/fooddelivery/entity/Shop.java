package com.example.fooddelivery.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("shops")
public class Shop {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
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
    private LocalDateTime updatedAt;
}