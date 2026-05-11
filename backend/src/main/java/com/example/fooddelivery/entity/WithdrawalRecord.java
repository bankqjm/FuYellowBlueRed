package com.example.fooddelivery.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("withdrawal_records")
public class WithdrawalRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private BigDecimal amount;
    private String method;
    private String account;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}