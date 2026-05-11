package com.example.fooddelivery.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.fooddelivery.entity.Shop;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ShopMapper extends BaseMapper<Shop> {
    List<Shop> findNearbyShops(Double latitude, Double longitude, Double radius);
    List<Shop> findByStatus(Integer status);
}