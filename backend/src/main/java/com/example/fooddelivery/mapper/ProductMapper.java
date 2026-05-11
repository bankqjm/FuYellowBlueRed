package com.example.fooddelivery.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.fooddelivery.entity.Product;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ProductMapper extends BaseMapper<Product> {
    List<Product> findByShopId(Long shopId);
    List<Product> findByCategoryId(Long categoryId);
    List<Product> searchProducts(String keyword);
}