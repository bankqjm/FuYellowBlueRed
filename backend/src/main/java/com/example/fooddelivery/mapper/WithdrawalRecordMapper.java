package com.example.fooddelivery.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.fooddelivery.entity.WithdrawalRecord;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface WithdrawalRecordMapper extends BaseMapper<WithdrawalRecord> {
    List<WithdrawalRecord> findByUserId(Long userId);
    List<WithdrawalRecord> findByStatus(String status);
}