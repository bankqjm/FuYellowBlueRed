package com.example.fooddelivery.service;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;

import java.util.List;

public interface ShopService {
    Shop createShop(Long userId, ShopCreateRequest request);
    Shop updateShop(Long shopId, ShopCreateRequest request);
    Shop findById(Long id);
    Shop findByUserId(Long userId);
    List<ShopResponse> findNearbyShops(Double latitude, Double longitude, Double radius);
    List<Shop> findByStatus(Integer status);
    void updateStatus(Long shopId, Integer status);
}