package com.example.fooddelivery.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("reviews")
public class Review {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long orderId;
    private Long userId;
    private Long shopId;
    private Long riderId;
    private Integer shopRating;
    private Integer riderRating;
    private String content;
    private String images;
    private LocalDateTime createdAt;
}