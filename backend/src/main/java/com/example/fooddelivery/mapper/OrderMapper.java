package com.example.fooddelivery.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.fooddelivery.entity.Order;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface OrderMapper extends BaseMapper<Order> {
    List<Order> findByUserId(Long userId);
    List<Order> findByShopId(Long shopId);
    List<Order> findByRiderId(Long riderId);
    List<Order> findPendingOrders();
    Order findByOrderNo(String orderNo);
}