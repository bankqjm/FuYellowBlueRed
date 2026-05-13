const puppeteer = require('puppeteer');
const path = require('path');

async function takeScreenshots() {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });

    // 登录页截图
    console.log('正在截取登录页...');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle0', timeout: 30000 });
    await page.screenshot({ path: '/workspace/docs/login-page.png', fullPage: false });
    console.log('登录页已保存到 /workspace/docs/login-page.png');

    // 首页截图 - 先登录
    console.log('正在截取首页...');
    // 填写登录表单
    await page.evaluate(() => {
        const phoneInput = document.querySelector('input[type="text"]') || document.querySelector('input[placeholder*="手机"]');
        const passwordInput = document.querySelector('input[type="password"]');
        if (phoneInput) phoneInput.value = '13900000001';
        if (passwordInput) passwordInput.value = 'user123';
    });

    await page.waitForTimeout(500);

    // 提交登录
    const loginButton = await page.$('button[type="submit"]');
    if (loginButton) {
        await loginButton.click();
        await page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 15000 }).catch(() => {});
    }

    // 等待页面加载
    await page.waitForTimeout(2000);

    // 截取首页
    await page.screenshot({ path: '/workspace/docs/home-page.png', fullPage: false });
    console.log('首页已保存到 /workspace/docs/home-page.png');

    await browser.close();
    console.log('截图完成!');
}

takeScreenshots().catch(console.error);
