package com.example.fooddelivery.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.fooddelivery.entity.RiderEarning;
import org.apache.ibatis.annotations.Mapper;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface RiderEarningMapper extends BaseMapper<RiderEarning> {
    List<RiderEarning> findByRiderId(Long riderId);
    BigDecimal sumEarningsByRiderId(Long riderId);
    BigDecimal sumEarningsByDate(Long riderId, LocalDateTime startTime, LocalDateTime endTime);
}