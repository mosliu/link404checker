from .base_plugin import BasePlugin
import re
from utils import logger, USER_AGENTS
import random
from bs4 import BeautifulSoup
import traceback
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import asyncio

class Plugin(BasePlugin):
    name = "toutiao"

    def match(self, url):
        # 匹配形如 "@https://www.toutiao.com/w/1804448956217344/" 的URL
        # return bool(re.match(r'^@?https?://(?:www\.)?toutiao\.com/w/\d+/?$', url))
        return bool(re.match(r'^@?https?://(?:www\.)?toutiao\.com/[a-zA-Z0-9]+/?.*$', url))

    def is_404(self, soup, title):
        # 检查标题是否为 "404错误页"
        if title == "404错误页":
            return True
        
        # 检查是否存在包含特定错误信息的段落
        error_tip = soup.find('p', class_='error-tips')
        if error_tip and "抱歉，你访问的内容不存在" in error_tip.text:
            return True
        
        return False

    def process(self, response):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={'width': 1280, 'height': 720}
                )
                page = context.new_page()
                
                # 设置 referer
                # page.set_extra_http_headers({'Referer': '@https://www.toutiao.com/'})

                logger.info(f"正在使用 Playwright 访问 URL: {response.url}")
                page.goto(response.url, wait_until='networkidle')
                
                logger.info(f"头条插件最终请求URL: {page.url}")
                
                # 解析页面内容
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # 提取标题
                title = soup.title.string if soup.title else "无标题"
                logger.info(f"提取的标题: {title}")
                
                # 检查是否为404
                if self.is_404(soup, title):
                    logger.info("检测到404 Not Found")
                    browser.close()
                    return {
                        "custom_field": "Toutiao plugin applied",
                        "status_code": 404,
                        # "headers": dict(page.request.headers()),
                        "final_url": page.url,
                        "title": "404 Not Found",
                        "content_preview": "页面不存在",
                        "full_content": "页面不存在"
                    }
                
                # 尝试提取正文
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
                    # "headers": dict(page.request.headers()),
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

    async def initialize(self):
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch()
            self.context = await self.browser.new_context()

    async def fetch_toutiao_news(self):
        await self.initialize()
        page = await self.context.new_page()
        # ... 其余代码保持不变 ...

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None

# 全局实例
toutiao_plugin = ToutiaoPlugin()

async def get_toutiao_news():
    return await toutiao_plugin.fetch_toutiao_news()
