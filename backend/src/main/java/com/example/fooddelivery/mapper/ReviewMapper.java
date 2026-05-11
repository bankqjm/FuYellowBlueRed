package com.example.fooddelivery.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.fooddelivery.entity.Review;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ReviewMapper extends BaseMapper<Review> {
    List<Review> findByShopId(Long shopId);
    List<Review> findByUserId(Long userId);
    Review findByOrderId(Long orderId);
}