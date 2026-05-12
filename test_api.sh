#!/bin/bash

BASE_URL="http://localhost:8000"
API_URL="$BASE_URL/api/v1"

echo "=========================================="
echo "   FuYellowBlueRed API 完整测试报告"
echo "=========================================="
echo "测试时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

PASSED=0
FAILED=0
TOTAL=0

test_api() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    local expected=$5
    local headers=$6

    TOTAL=$((TOTAL + 1))

    if [ "$method" = "GET" ]; then
        if [ -n "$headers" ]; then
            response=$(curl -s -w "\n%{http_code}" -H "$headers" "$url")
        else
            response=$(curl -s -w "\n%{http_code}" "$url")
        fi
    else
        if [ -n "$headers" ]; then
            response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" -H "$headers" -d "$data" "$url")
        else
            response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url")
        fi
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if echo "$http_code" | grep -q "$expected"; then
        echo "✅ [$method] $name - 通过 (HTTP $http_code)"
        PASSED=$((PASSED + 1))
    else
        echo "❌ [$method] $name - 失败"
        echo "   预期: $expected, 实际: $http_code"
        echo "   响应: $body" | head -c 200
        echo ""
        FAILED=$((FAILED + 1))
    fi
}

echo "=========================================="
echo "【1. 基础健康检查】"
echo "=========================================="
test_api "健康检查" "GET" "$BASE_URL/health" "" "200"
test_api "根路径" "GET" "$BASE_URL/" "" "200"
echo ""

echo "=========================================="
echo "【2. 认证模块测试 - 预置账户】"
echo "=========================================="
echo "使用预置测试账户登录..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" -H "Content-Type: application/json" -d '{"phone":"13900000001","password":"user123"}')
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
if [ -n "$TOKEN" ]; then
    echo "✅ 用户登录-成功 | Token: ${TOKEN:0:20}..."
    PASSED=$((PASSED + 1))
else
    echo "❌ 用户登录-失败: $LOGIN_RESPONSE"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

echo ""
RIDER_LOGIN=$(curl -s -X POST "$API_URL/auth/login" -H "Content-Type: application/json" -d '{"phone":"13900000003","password":"rider123"}')
RIDER_TOKEN=$(echo "$RIDER_LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
if [ -n "$RIDER_TOKEN" ]; then
    echo "✅ 骑手登录-成功 | Token: ${RIDER_TOKEN:0:20}..."
    PASSED=$((PASSED + 1))
else
    echo "❌ 骑手登录-失败"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

echo ""
ADMIN_LOGIN=$(curl -s -X POST "$API_URL/auth/login" -H "Content-Type: application/json" -d '{"phone":"13800000000","password":"admin123"}')
ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
if [ -n "$ADMIN_TOKEN" ]; then
    echo "✅ 管理员登录-成功 | Token: ${ADMIN_TOKEN:0:20}..."
    PASSED=$((PASSED + 1))
else
    echo "❌ 管理员登录-失败"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))
echo ""

echo "=========================================="
echo "【3. 用户模块测试】"
echo "=========================================="
AUTH_HEADER="Authorization: Bearer $TOKEN"

test_api "获取当前用户信息" "GET" "$API_URL/users/me" "" "200" "$AUTH_HEADER"
test_api "获取用户信息-无Token" "GET" "$API_URL/users/me" "" "401"
test_api "获取用户信息-无效Token" "GET" "$API_URL/users/me" "" "401" "Authorization: Bearer invalid_token"
echo ""

echo "=========================================="
echo "【4. 地址管理测试】"
echo "=========================================="
test_api "获取地址列表" "GET" "$API_URL/users/addresses" "" "200" "$AUTH_HEADER"
echo ""

echo "=========================================="
echo "【5. 商家模块测试】"
echo "=========================================="
test_api "商家列表" "GET" "$API_URL/shop/list?page=1&page_size=10" "" "200"
test_api "商家详情-存在" "GET" "$API_URL/shop/1" "" "200"
test_api "商家详情-ID不存在" "GET" "$API_URL/shop/99999" "" "400"
test_api "商家分类列表" "GET" "$API_URL/shop/categories" "" "200"
echo ""

echo "=========================================="
echo "【6. 商品模块测试】"
echo "=========================================="
test_api "商品列表-按商家" "GET" "$API_URL/shop/product/1?page=1&page_size=10" "" "200"
test_api "商品列表-按商家和分类" "GET" "$API_URL/shop/product/1?category_id=1&page=1" "" "200"
test_api "商品详情-存在" "GET" "$API_URL/shop/product/detail/1" "" "200"
test_api "商品详情-不存在" "GET" "$API_URL/shop/product/detail/99999" "" "400"
echo ""

echo "=========================================="
echo "【7. 购物车测试】"
echo "=========================================="
test_api "获取购物车" "GET" "$API_URL/orders/cart" "" "200" "$AUTH_HEADER"
test_api "获取购物车-无Token" "GET" "$API_URL/orders/cart" "" "401"
echo ""

echo "=========================================="
echo "【8. 订单流程测试】"
echo "=========================================="
test_api "获取订单列表" "GET" "$API_URL/orders" "" "200" "$AUTH_HEADER"
test_api "获取订单列表-无Token" "GET" "$API_URL/orders" "" "401"
test_api "订单详情-ID不存在" "GET" "$API_URL/orders/99999" "" "400" "$AUTH_HEADER"
echo ""

echo "=========================================="
echo "【9. 骑手模块测试】"
echo "=========================================="
RIDER_HEADER="Authorization: Bearer $RIDER_TOKEN"
test_api "骑手-接单列表" "GET" "$API_URL/rider/orders/available" "" "200" "$RIDER_HEADER"
test_api "骑手-活跃订单" "GET" "$API_URL/rider/orders/active" "" "200" "$RIDER_HEADER"
test_api "骑手-收入统计" "GET" "$API_URL/rider/earnings" "" "200" "$RIDER_HEADER"
test_api "骑手-收入汇总" "GET" "$API_URL/rider/earnings/summary" "" "200" "$RIDER_HEADER"
test_api "骑手-提现记录" "GET" "$API_URL/rider/withdrawals" "" "200" "$RIDER_HEADER"
echo ""

echo "=========================================="
echo "【10. 骑手模块-用户角色权限测试】"
echo "=========================================="
test_api "普通用户-骑手接口-权限不足" "GET" "$API_URL/rider/orders/available" "" "403" "$AUTH_HEADER"
test_api "普通用户-骑手收入-权限不足" "GET" "$API_URL/rider/earnings" "" "403" "$AUTH_HEADER"
echo ""

echo "=========================================="
echo "【11. 评价模块测试】"
echo "=========================================="
test_api "添加评价-无Token" "POST" "$API_URL/reviews" '{"order_id":1,"shop_rating":5,"content":"好评"}' "401"
test_api "获取商家评价" "GET" "$API_URL/reviews/shop/1" "" "200"
test_api "获取订单评价-暂无评价" "GET" "$API_URL/reviews/order/1" "" "400"
echo ""

echo "=========================================="
echo "【12. 管理后台测试】"
echo "=========================================="
ADMIN_HEADER="Authorization: Bearer $ADMIN_TOKEN"
test_api "管理员-获取用户列表" "GET" "$API_URL/admin/users" "" "200" "$ADMIN_HEADER"
test_api "管理员-待审核商家列表" "GET" "$API_URL/admin/shop/pending" "" "200" "$ADMIN_HEADER"
test_api "管理员-平台统计" "GET" "$API_URL/admin/stats" "" "200" "$ADMIN_HEADER"
echo ""

echo "=========================================="
echo "【13. 管理后台-用户角色权限测试】"
echo "=========================================="
test_api "普通用户-管理员接口-权限不足" "GET" "$API_URL/admin/users" "" "403" "$AUTH_HEADER"
test_api "骑手-管理员接口-权限不足" "GET" "$API_URL/admin/users" "" "403" "$RIDER_HEADER"
echo ""

echo "=========================================="
echo "【14. 文件上传测试】"
echo "=========================================="
test_api "上传文件-无Token" "POST" "$API_URL/upload" "" "401"
echo ""

echo "=========================================="
echo "【15. 边界条件测试】"
echo "=========================================="
test_api "商家列表-分页参数为0" "GET" "$API_URL/shop/list?page=0" "" "422"
test_api "商家列表-分页大小超限" "GET" "$API_URL/shop/list?page_size=1000" "" "422"
test_api "商品列表-分页参数正常" "GET" "$API_URL/shop/product/1?page=1&page_size=10" "" "200"
echo ""

echo "=========================================="
echo "【16. 完整订单流程测试】"
echo "=========================================="
echo "添加商品到购物车..."
CART_RESPONSE=$(curl -s -X POST "$API_URL/orders/cart" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{"product_id":1,"shop_id":1,"quantity":2}')
CART_CODE=$(echo "$CART_RESPONSE" | grep -o '"code":[0-9]*' | cut -d':' -f2)
if [ "$CART_CODE" = "0" ]; then
    echo "✅ 添加购物车-成功"
    PASSED=$((PASSED + 1))
else
    echo "❌ 添加购物车-失败: $CART_RESPONSE"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))
echo ""

echo "=========================================="
echo "测试结果汇总"
echo "=========================================="
echo "总测试数: $TOTAL"
echo "通过: $PASSED"
echo "失败: $FAILED"
echo "通过率: $(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")%"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo "🎉 所有测试通过！"
    exit 0
else
    echo "⚠️  有 $FAILED 项测试失败"
    exit 1
fi
