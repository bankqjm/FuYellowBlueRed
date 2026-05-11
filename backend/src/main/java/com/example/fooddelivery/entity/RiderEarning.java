package com.example.fooddelivery.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("rider_earnings")
public class RiderEarning {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long riderId;
    private Long orderId;
    private BigDecimal amount;
    private String type;
    private LocalDateTime createdAt;
}