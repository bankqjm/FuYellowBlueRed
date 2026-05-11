packagepackage com.example.fooddelivery.service.impl;

importpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreatepackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dtopackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.examplepackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopServicepackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Colpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class Shoppackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final Shoppackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Longpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shoppackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHourspackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZEROpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId,package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shopMapper.updateById(shop);
        return shoppackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shopMapper.updateById(shop);
        return shop;
    }

    @Override
    public Shop findById(Long id) {
        return shopMapper.selectById(id);
package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shopMapper.updateById(shop);
        return shop;
    }

    @Override
    public Shop findById(Long id) {
        return shopMapper.selectById(id);
    }

    @Override
    public Shop findBypackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shopMapper.updateById(shop);
        return shop;
    }

    @Override
    public Shop findById(Long id) {
        return shopMapper.selectById(id);
    }

    @Override
    public Shop findByUserId(Long userId) {
        return shopMapperpackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shopMapper.updateById(shop);
        return shop;
    }

    @Override
    public Shop findById(Long id) {
        return shopMapper.selectById(id);
    }

    @Override
    public Shop findByUserId(Long userId) {
        return shopMapper.selectOne(new com.baomidou.mybatispackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shopMapper.updateById(shop);
        return shop;
    }

    @Override
    public Shop findById(Long id) {
        return shopMapper.selectById(id);
    }

    @Override
    public Shop findByUserId(Long userId) {
        return shopMapper.selectOne(new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<Shop>()
                .eq("user_id", userId));package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shopMapper.updateById(shop);
        return shop;
    }

    @Override
    public Shop findById(Long id) {
        return shopMapper.selectById(id);
    }

    @Override
    public Shop findByUserId(Long userId) {
        return shopMapper.selectOne(new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<Shop>()
                .eq("user_id", userId));
package com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shopMapper.updateById(shop);
        return shop;
    }

    @Override
    public Shop findById(Long id) {
        return shopMapper.selectById(id);
    }

    @Override
    public Shop findByUserId(Long userId) {
        return shopMapper.selectOne(new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<Shop>()
                .eq("user_id", userId));
    }

    @Override
    public List<ShopResponse> findNearbyShops(Doublepackage com.example.fooddelivery.service.impl;

import com.example.fooddelivery.dto.request.ShopCreateRequest;
import com.example.fooddelivery.dto.response.ShopResponse;
import com.example.fooddelivery.entity.Shop;
import com.example.fooddelivery.mapper.ShopMapper;
import com.example.fooddelivery.service.ShopService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ShopServiceImpl implements ShopService {

    private final ShopMapper shopMapper;

    public ShopServiceImpl(ShopMapper shopMapper) {
        this.shopMapper = shopMapper;
    }

    @Override
    public Shop createShop(Long userId, ShopCreateRequest request) {
        Shop shop = new Shop();
        shop.setUserId(userId);
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shop.setStatus(0);
        shop.setRating(java.math.BigDecimal.ZERO);
        shopMapper.insert(shop);
        return shop;
    }

    @Override
    public Shop updateShop(Long shopId, ShopCreateRequest request) {
        Shop shop = shopMapper.selectById(shopId);
        if (shop == null) {
            throw new RuntimeException("店铺不存在");
        }
        shop.setName(request.getName());
        shop.setLogo(request.getLogo());
        shop.setAddress(request.getAddress());
        shop.setLatitude(request.getLatitude());
        shop.setLongitude(request.getLongitude());
        shop.setBusinessHours(request.getBusinessHours());
        shop.setNotice(request.getNotice());
        shopMapper.updateById(shop);
        return shop;
    }

    @Override
    public Shop findById(Long id) {
        return shopMapper.selectById(id);
    }

    @Override
    public Shop findByUserId(Long userId) {
        return shopMapper.selectOne(new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<Shop>()
                .eq("user_id", userId));
    }

    @Override
    public List<ShopResponse> findNearbyShops(Double latitude, Double longitude, Double radius) {
        List<Shop> shops = shopMapper.findNear