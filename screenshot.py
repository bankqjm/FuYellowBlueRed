import asyncio
from playwright.async_api import async_playwright
import os

async def take_screenshots():
    # 首先检查浏览器是否已安装
    try:
        async with async_playwright() as p:
            # 尝试启动chromium
            try:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
                )
            except Exception as e:
                print(f"启动浏览器失败: {e}")
                print("尝试下载 Chromium...")
                await p.chromium.download()
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
                )

            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})

            # 登录页截图
            print('正在截取登录页...')
            await page.goto('http://localhost:3000/login', wait_until='networkidle', timeout=30000)
            await page.screenshot(path='/workspace/docs/login-page.png')
            print('登录页已保存')

            # 登录并截取首页
            print('正在登录...')
            await page.fill('input[type="text"]', '13900000001')
            await page.fill('input[type="password"]', 'user123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(2)

            await page.screenshot(path='/workspace/docs/home-page.png')
            print('首页已保存')

            await browser.close()
            print('完成!')

    except Exception as e:
        print(f"错误: {e}")
        # 备用方案：使用curl保存HTML
        import subprocess
        subprocess.run(['curl', '-s', 'http://localhost:3000/login', '-o', '/workspace/docs/login-page.html'])
        print("已保存登录页HTML到 /workspace/docs/login-page.html")

if __name__ == '__main__':
    asyncio.run(take_screenshots())
