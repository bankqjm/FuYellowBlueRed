package com.example.fooddelivery.dto.response;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Data
public class OrderResponse {
    private Long id;
    private String orderNo;
    private Long shopId;
    private String shopName;
    private String shopLogo;
    private Long riderId;
    private String riderName;
    private String riderPhone;
    private String address;
    private BigDecimal latitude;
    private BigDecimal longitude;
    private String phone;
    private String remark;
    private BigDecimal totalAmount;
    private BigDecimal deliveryFee;
    private String status;
    private String statusText;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private List<OrderItemResponse> items;

    @Data
    public static class OrderItemResponse {
        private Long id;
        private String productName;
        private String productImage;
        private BigDecimal price;
        private Integer quantity;
    }
}