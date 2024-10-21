from .base_plugin import BasePlugin
import re
from utils import logger, USER_AGENTS, get_proxy
import random
from bs4 import BeautifulSoup
import traceback
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import asyncio
from config import USE_PROXY

class Plugin(BasePlugin):
    name = "toutiao"
    current_proxy = None

    def match(self, url):
        return bool(re.match(r'^@?https?://(?:www\.)?toutiao\.com/[a-zA-Z0-9]+/?.*$', url))

    def is_404(self, soup, title):
        if title == "404错误页":
            return True
        
        error_tip = soup.find('p', class_='error-tips')
        if error_tip and "抱歉，你访问的内容不存在" in error_tip.text:
            return True
        
        return False

    def update_proxy(self, context):
        if USE_PROXY:
            new_proxy = get_proxy()
            if new_proxy != self.current_proxy:
                logger.info(f"更新代理: {new_proxy}")
                context.set_extra_http_headers({"proxy": new_proxy})
                self.current_proxy = new_proxy

    def process(self, response):
        try:
            with sync_playwright() as p:
                browser_type = p.chromium
                browser = browser_type.launch(headless=True)
                context = browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={'width': 1280, 'height': 720}
                )
                
                self.update_proxy(context)
                
                page = context.new_page()

                logger.info(f"正在使用 Playwright 访问 URL: {response.url}")
                page.goto(response.url, wait_until='networkidle')
                
                logger.info(f"头条插件最终请求URL: {page.url}")
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                title = soup.title.string if soup.title else "无标题"
                logger.info(f"提取的标题: {title}")
                
                if self.is_404(soup, title):
                    logger.info("检测到404 Not Found")
                    browser.close()
                    return {
                        "custom_field": "Toutiao plugin applied",
                        "status_code": 404,
                        "final_url": page.url,
                        "title": "404 Not Found",
                        "content_preview": "页面不存在",
                        "full_content": "页面不存在"
                    }
                
                content = soup.find('div', class_='article-content') or \
                          soup.find('div', id='article-content') or \
                          soup.find('div', id='main-content') or \
                          soup.find('article')
                
                if content:
                    content_text = content.get_text(strip=True)
                    logger.info(f"成功提取正文，长度: {len(content_text)}")
                else:
                    content_text = "无法提取正文"
                    logger.warning("无法找到正文内容")
                
                logger.info(f"头条插件提取的正文预览: {content_text[:200]}...")
                
                browser.close()
                
                return {
                    "custom_field": "Toutiao plugin applied",
                    "status_code": 200,  # Playwright 不直接提供状态码，所以我们假设成功
                    "final_url": page.url,
                    "title": title,
                    "content_preview": content_text[:200],
                    "full_content": content_text
                }
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(f"头条插件请求失败: {str(e)}\n堆栈跟踪:\n{stack_trace}")
            return {
                "custom_field": "Toutiao plugin error",
                "error": str(e),
                "status_code": None
            }

class ToutiaoPlugin:
    def __init__(self):
        self.browser = None
        self.context = None
        self.current_proxy = None

    async def initialize(self):
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch()
            self.context = await self.browser.new_context()
        
        if USE_PROXY:
            new_proxy = get_proxy()
            if new_proxy != self.current_proxy:
                logger.info(f"更新代理: {new_proxy}")
                await self.context.set_extra_http_headers({"proxy": new_proxy})
                self.current_proxy = new_proxy

    async def fetch_toutiao_news(self):
        await self.initialize()
        page = await self.context.new_page()
        # ... 其余代码保持不变 ...

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.current_proxy = None

# 全局实例
toutiao_plugin = ToutiaoPlugin()

async def get_toutiao_news():
    return await toutiao_plugin.fetch_toutiao_news()
