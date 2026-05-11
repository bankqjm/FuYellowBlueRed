package com.example.fooddelivery.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("orders")
public class Order {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String orderNo;
    private Long userId;
    private Long shopId;
    private Long riderId;
    private String address;
    private BigDecimal latitude;
    private BigDecimal longitude;
    private String phone;
    private String remark;
    private BigDecimal totalAmount;
    private BigDecimal deliveryFee;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}