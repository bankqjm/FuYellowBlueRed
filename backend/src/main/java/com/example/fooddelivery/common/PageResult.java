package com.example.fooddelivery.common;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PageResult<T> {
    private List<T> records;
    private Long total;
    private Integer pageSize;
    private Integer currentPage;

    public static <T> PageResult<T> success(List<T> records, Long total, Integer pageSize, Integer currentPage) {
        return new PageResult<>(records, total, pageSize, currentPage);
    }
}