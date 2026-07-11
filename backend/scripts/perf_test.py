"""
性能压测脚本
核心业务流程：用户浏览 → 下单 → 支付 → 骑手接单
目标：10分钟，500TPM
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import time
import random
import json
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import httpx


# ============ 配置 ============
BASE_URL = "http://localhost:8000/api/v1"
DURATION_SECONDS = 600  # 10分钟
TARGET_TPM = 500  # 每分钟500笔
CONCURRENT_USERS = 50  # 并发用户数

# 压测用户范围（数据准备时创建的1000个用户，手机号前缀150）
USER_PHONE_PREFIX = "150"
USER_COUNT = 1000
USER_PASSWORD = "Test123456"

# ============ 压测案例 ============

class PerfTest:
    def __init__(self):
        self.results = {
            "browse_shops": [],
            "shop_detail": [],
            "create_order": [],
            "pay_order": [],
            "rider_accept": [],
            "login": [],
            "wallet_query": [],
            "favorites": [],
        }
        self.errors = []
        self.total_requests = 0
        self.success_requests = 0
        self.start_time = None
        self.tokens = {}  # user_index -> token
        self.shop_ids = []
        self.rider_tokens = {}
        self.lock = asyncio.Lock()

    async def login_user(self, client: httpx.AsyncClient, user_index: int) -> str:
        """用户登录获取token"""
        phone = f"{USER_PHONE_PREFIX}{str(user_index+1).zfill(8)}"
        r = await client.post(f"{BASE_URL}/auth/login", json={
            "phone": phone,
            "password": USER_PASSWORD,
        })
        if r.status_code == 200:
            return r.json()["data"]["access_token"]
        return None

    async def login_rider(self, client: httpx.AsyncClient, rider_index: int) -> str:
        """骑手登录"""
        phone = f"152{str(rider_index+1).zfill(8)}"
        r = await client.post(f"{BASE_URL}/auth/login", json={
            "phone": phone,
            "password": USER_PASSWORD,
        })
        if r.status_code == 200:
            return r.json()["data"]["access_token"]
        return None

    async def setup(self):
        """初始化：预登录部分用户，获取店铺列表"""
        print("初始化压测环境...")
        async with httpx.AsyncClient(timeout=60) as client:
            # 分批预登录用户（每批20个）
            print("  预登录用户...")
            for batch_start in range(0, min(200, USER_COUNT), 20):
                batch_end = min(batch_start + 20, USER_COUNT)
                login_tasks = [self.login_user(client, i) for i in range(batch_start, batch_end)]
                tokens = await asyncio.gather(*login_tasks)
                for i, token in enumerate(tokens):
                    if token:
                        self.tokens[batch_start + i] = token
                print(f"    已登录 {len(self.tokens)} 个用户...")
            print(f"  共登录 {len(self.tokens)} 个用户")

            # 获取店铺列表
            if self.tokens:
                token = list(self.tokens.values())[0]
                r = await client.get(f"{BASE_URL}/shop/list", headers={"Authorization": f"Bearer {token}"})
                if r.status_code == 200:
                    shops = r.json().get("data", {}).get("items", [])
                    self.shop_ids = [s["id"] for s in shops]
                    print(f"  获取到 {len(self.shop_ids)} 个店铺")

            # 预登录骑手
            print("  预登录骑手...")
            for i in range(min(20, 100)):
                token = await self.login_rider(client, i)
                if token:
                    self.rider_tokens[i] = token
            print(f"  已登录 {len(self.rider_tokens)} 个骑手")

    async def record_result(self, case_name: str, elapsed_ms: float, status_code: int, error: str = None):
        async with self.lock:
            self.total_requests += 1
            if not error and 200 <= status_code < 400:
                self.success_requests += 1
            self.results[case_name].append({
                "elapsed_ms": elapsed_ms,
                "status_code": status_code,
                "timestamp": time.time(),
                "error": error,
            })
            if error:
                self.errors.append(f"{case_name}: {error}")

    # ============ 压测案例实现 ============

    async def case_browse_shops(self, client: httpx.AsyncClient, token: str):
        """案例1：浏览店铺列表"""
        start = time.time()
        try:
            r = await client.get(f"{BASE_URL}/shop/list", headers={"Authorization": f"Bearer {token}"})
            elapsed = (time.time() - start) * 1000
            await self.record_result("browse_shops", elapsed, r.status_code)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            await self.record_result("browse_shops", elapsed, 0, str(e))

    async def case_shop_detail(self, client: httpx.AsyncClient, token: str):
        """案例2：查看店铺详情"""
        if not self.shop_ids:
            return
        shop_id = random.choice(self.shop_ids)
        start = time.time()
        try:
            r = await client.get(f"{BASE_URL}/shop/{shop_id}", headers={"Authorization": f"Bearer {token}"})
            elapsed = (time.time() - start) * 1000
            await self.record_result("shop_detail", elapsed, r.status_code)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            await self.record_result("shop_detail", elapsed, 0, str(e))

    async def case_wallet_query(self, client: httpx.AsyncClient, token: str):
        """案例3：查询钱包"""
        start = time.time()
        try:
            r = await client.get(f"{BASE_URL}/wallet", headers={"Authorization": f"Bearer {token}"})
            elapsed = (time.time() - start) * 1000
            await self.record_result("wallet_query", elapsed, r.status_code)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            await self.record_result("wallet_query", elapsed, 0, str(e))

    async def case_favorites(self, client: httpx.AsyncClient, token: str):
        """案例4：查询收藏列表"""
        start = time.time()
        try:
            r = await client.get(f"{BASE_URL}/favorites", headers={"Authorization": f"Bearer {token}"})
            elapsed = (time.time() - start) * 1000
            await self.record_result("favorites", elapsed, r.status_code)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            await self.record_result("favorites", elapsed, 0, str(e))

    async def case_create_and_pay_order(self, client: httpx.AsyncClient, token: str):
        """案例5：创建订单+支付（完整下单流程）"""
        if not self.shop_ids:
            return
        shop_id = random.choice(self.shop_ids)

        # 5a: 获取店铺详情（含商品）
        start = time.time()
        try:
            r = await client.get(f"{BASE_URL}/shop/{shop_id}", headers={"Authorization": f"Bearer {token}"})
            elapsed = (time.time() - start) * 1000
            await self.record_result("shop_detail", elapsed, r.status_code)
        except Exception as e:
            return

        # 5b: 获取购物车
        try:
            r = await client.get(f"{BASE_URL}/orders/cart", headers={"Authorization": f"Bearer {token}"})
        except:
            pass

        # 5c: 获取地址
        try:
            r = await client.get(f"{BASE_URL}/users/addresses", headers={"Authorization": f"Bearer {token}"})
            addresses = r.json().get("data", [])
            address_id = addresses[0]["id"] if addresses else None
        except:
            address_id = None

        # 5d: 创建订单
        start = time.time()
        try:
            r = await client.post(f"{BASE_URL}/orders/create", json={
                "shop_id": shop_id,
                "address_id": address_id,
                "remark": "压测订单",
            }, headers={"Authorization": f"Bearer {token}"})
            elapsed = (time.time() - start) * 1000
            await self.record_result("create_order", elapsed, r.status_code)

            if r.status_code == 200:
                order_id = r.json().get("data", {}).get("id")
                if order_id:
                    # 5e: 支付订单
                    start = time.time()
                    try:
                        r = await client.post(f"{BASE_URL}/orders/{order_id}/pay", json={"channel": "BALANCE"},
                                              headers={"Authorization": f"Bearer {token}"})
                        elapsed = (time.time() - start) * 1000
                        await self.record_result("pay_order", elapsed, r.status_code)
                    except Exception as e:
                        elapsed = (time.time() - start) * 1000
                        await self.record_result("pay_order", elapsed, 0, str(e))
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            await self.record_result("create_order", elapsed, 0, str(e))

    async def case_rider_accept(self, client: httpx.AsyncClient, rider_token: str):
        """案例6：骑手接单"""
        start = time.time()
        try:
            r = await client.get(f"{BASE_URL}/rider/orders/available",
                                 headers={"Authorization": f"Bearer {rider_token}"})
            if r.status_code == 200:
                orders = r.json().get("data", [])
                if orders:
                    order_id = orders[0]["id"]
                    r2 = await client.put(f"{BASE_URL}/rider/orders/{order_id}/accept",
                                          headers={"Authorization": f"Bearer {rider_token}"})
                    elapsed = (time.time() - start) * 1000
                    await self.record_result("rider_accept", elapsed, r2.status_code)
                else:
                    elapsed = (time.time() - start) * 1000
                    await self.record_result("rider_accept", elapsed, 200)
            else:
                elapsed = (time.time() - start) * 1000
                await self.record_result("rider_accept", elapsed, r.status_code)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            await self.record_result("rider_accept", elapsed, 0, str(e))

    # ============ 压测执行器 ============

    async def worker(self, worker_id: int, duration: int):
        """单个并发worker"""
        async with httpx.AsyncClient(timeout=60) as client:
            end_time = time.time() + duration
            user_index = worker_id % len(self.tokens)
            token = self.tokens.get(user_index)
            if not token:
                return

            while time.time() < end_time:
                # 按权重随机选择案例
                case = random.choices(
                    ["browse", "detail", "wallet", "favorites", "order", "rider"],
                    weights=[30, 25, 15, 10, 15, 5],
                    k=1
                )[0]

                if case == "browse":
                    await self.case_browse_shops(client, token)
                elif case == "detail":
                    await self.case_shop_detail(client, token)
                elif case == "wallet":
                    await self.case_wallet_query(client, token)
                elif case == "favorites":
                    await self.case_favorites(client, token)
                elif case == "order":
                    await self.case_create_and_pay_order(client, token)
                elif case == "rider":
                    rider_token = random.choice(list(self.rider_tokens.values())) if self.rider_tokens else None
                    if rider_token:
                        await self.case_rider_accept(client, rider_token)

                # 控制请求频率
                await asyncio.sleep(random.uniform(0.05, 0.2))

    async def run(self):
        """执行压测"""
        await self.setup()

        print(f"\n{'='*60}")
        print(f"压测开始")
        print(f"  持续时间: {DURATION_SECONDS}秒 ({DURATION_SECONDS//60}分钟)")
        print(f"  目标TPM: {TARGET_TPM}")
        print(f"  并发用户: {CONCURRENT_USERS}")
        print(f"  可用token: {len(self.tokens)} 用户 + {len(self.rider_tokens)} 骑手")
        print(f"{'='*60}\n")

        self.start_time = time.time()

        # 启动并发workers
        workers = [self.worker(i, DURATION_SECONDS) for i in range(CONCURRENT_USERS)]
        await asyncio.gather(*workers)

        # 生成报告
        self.generate_report()

    def generate_report(self):
        """生成压测报告"""
        total_duration = time.time() - self.start_time

        print(f"\n{'='*60}")
        print(f"性能压测报告")
        print(f"{'='*60}")
        print(f"压测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"持续时长: {total_duration:.1f}秒 ({total_duration/60:.1f}分钟)")
        print(f"总请求数: {self.total_requests}")
        print(f"成功请求数: {self.success_requests}")
        print(f"失败请求数: {self.total_requests - self.success_requests}")
        print(f"错误率: {(self.total_requests - self.success_requests) / max(self.total_requests, 1) * 100:.2f}%")
        print(f"实际TPM: {self.total_requests / (total_duration / 60):.1f}")
        print(f"实际TPS: {self.total_requests / total_duration:.1f}")

        print(f"\n{'='*60}")
        print(f"各案例性能指标")
        print(f"{'='*60}")
        print(f"{'案例':<20} {'请求数':>8} {'平均(ms)':>10} {'P50(ms)':>10} {'P90(ms)':>10} {'P99(ms)':>10} {'最大(ms)':>10}")
        print("-" * 80)

        for case_name, records in self.results.items():
            if not records:
                continue
            latencies = [r["elapsed_ms"] for r in records]
            latencies.sort()
            avg = statistics.mean(latencies)
            p50 = latencies[int(len(latencies) * 0.5)]
            p90 = latencies[int(len(latencies) * 0.9)]
            p99 = latencies[int(len(latencies) * 0.99)]
            max_lat = max(latencies)
            errors = sum(1 for r in records if r.get("error"))
            print(f"{case_name:<20} {len(records):>8} {avg:>10.1f} {p50:>10.1f} {p90:>10.1f} {p99:>10.1f} {max_lat:>10.1f}")

        # 错误统计
        if self.errors:
            print(f"\n{'='*60}")
            print(f"错误统计 (前20条)")
            print(f"{'='*60}")
            for err in self.errors[:20]:
                print(f"  {err[:100]}")

        # 性能评估
        print(f"\n{'='*60}")
        print(f"性能评估")
        print(f"{'='*60}")
        actual_tpm = self.total_requests / (total_duration / 60)
        error_rate = (self.total_requests - self.success_requests) / max(self.total_requests, 1) * 100

        print(f"  TPM目标: {TARGET_TPM} | 实际: {actual_tpm:.1f} | {'✓ 达标' if actual_tpm >= TARGET_TPM else '✗ 未达标'}")
        print(f"  错误率: {error_rate:.2f}% | {'✓ 达标(<5%)' if error_rate < 5 else '✗ 未达标(>=5%)'}")

        # 各案例P90评估
        for case_name, records in self.results.items():
            if not records:
                continue
            latencies = [r["elapsed_ms"] for r in records]
            latencies.sort()
            p90 = latencies[int(len(latencies) * 0.9)]
            status = "✓ 优秀" if p90 < 200 else ("✓ 良好" if p90 < 500 else ("⚠ 一般" if p90 < 1000 else "✗ 需优化"))
            print(f"  {case_name} P90: {p90:.1f}ms {status}")

        # 保存报告到文件
        report_file = os.path.join(os.path.dirname(__file__), "perf_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": total_duration,
                "total_requests": self.total_requests,
                "success_requests": self.success_requests,
                "actual_tpm": actual_tpm,
                "actual_tps": self.total_requests / total_duration,
                "error_rate": error_rate,
                "results": {
                    name: {
                        "count": len(records),
                        "avg_ms": statistics.mean([r["elapsed_ms"] for r in records]) if records else 0,
                        "p50_ms": sorted([r["elapsed_ms"] for r in records])[int(len(records)*0.5)] if records else 0,
                        "p90_ms": sorted([r["elapsed_ms"] for r in records])[int(len(records)*0.9)] if records else 0,
                        "p99_ms": sorted([r["elapsed_ms"] for r in records])[int(len(records)*0.99)] if records else 0,
                    }
                    for name, records in self.results.items() if records
                },
                "errors_count": len(self.errors),
            }, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存至: {report_file}")


if __name__ == "__main__":
    test = PerfTest()
    asyncio.run(test.run())
