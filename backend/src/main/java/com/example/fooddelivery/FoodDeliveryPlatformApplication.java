package com.example.fooddelivery;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.example.fooddelivery.mapper")
public class FoodDeliveryPlatformApplication {

    public static void main(String[] args) {
        SpringApplication.run(FoodDeliveryPlatformApplication.class, args);
    }
}