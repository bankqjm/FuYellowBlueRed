package com.example.fooddelivery.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

@Data
public class OrderCreateRequest {
    @NotNull(message = "店铺ID不能为空")
    private Long shopId;
    @NotBlank(message = "送餐地址不能为空")
    private String address;
    private BigDecimal latitude;
    private BigDecimal longitude;
    @NotBlank(message = "联系电话不能为空")
    private String phone;
    private String remark;
    @NotNull(message = "商品列表不能为空")
    private List<OrderItemRequest> items;

    @Data
    public static class OrderItemRequest {
        @NotNull(message = "商品ID不能为空")
        private Long productId;
        @NotNull(message = "数量不能为空")
        @Positive(message = "数量必须大于0")
        private Integer quantity;
    }
}