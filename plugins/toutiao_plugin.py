from .base_plugin import BasePlugin
import re
import requests
from utils import site_cookies, get_site_cookies, logger, USER_AGENTS
import random
from bs4 import BeautifulSoup

class Plugin(BasePlugin):
    name = "toutiao"

    def match(self, url):
        # 匹配形如 "@https://www.toutiao.com/w/1804448956217344/" 的URL
        return bool(re.match(r'^@?https?://(?:www\.)?toutiao\.com/w/\d+/?$', url))

    def follow_redirect(self, url, max_redirects=5):
        for i in range(max_redirects):
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Upgrade-Insecure-Requests': '1',
            }
            logger.info(f"重定向 {i+1}: 请求 URL: {url}")
            response = requests.get(url, headers=headers, cookies=site_cookies.get('toutiao'), allow_redirects=False, timeout=10)
            logger.info(f"重定向 {i+1}: 状态码: {response.status_code}")
            
            if response.status_code in (301, 302, 303, 307, 308):
                url = response.headers.get('Location')
                if not url.startswith('http'):
                    url = f"https://www.toutiao.com{url}"
                logger.info(f"跟随重定向到: {url}")
            else:
                return response
        
        logger.warning(f"达到最大重定向次数 ({max_redirects})")
        return response

    def process(self, response):
        if 'toutiao' not in site_cookies or not site_cookies['toutiao']:
            get_site_cookies('toutiao', 'https://www.toutiao.com/')
        
        # 打印添加的cookies
        if site_cookies.get('toutiao'):
            logger.info(f"头条插件添加的cookies: {dict(site_cookies['toutiao'])}")
        else:
            logger.warning("头条cookies为空")
        
        try:
            # 跟随重定向并获取最终响应
            final_response = self.follow_redirect(response.url)
            
            logger.info(f"头条插件最终请求响应状态码: {final_response.status_code}")
            logger.info(f"头条插件最终请求响应头: {dict(final_response.headers)}")
            logger.info(f"头条插件最终请求URL: {final_response.url}")
            
            # 如果状态码是404，直接返回结果
            if final_response.status_code == 404:
                logger.info("遇到404 Not Found，不进行内容解析")
                return {
                    "custom_field": "Toutiao plugin applied",
                    "cookies_added": bool(site_cookies.get('toutiao')),
                    "status_code": 404,
                    "headers": dict(final_response.headers),
                    "final_url": final_response.url,
                    "title": "404 Not Found",
                    "content_preview": "页面不存在",
                    "full_content": "页面不存在"
                }
            
            # 解析页面内容
            soup = BeautifulSoup(final_response.text, 'html.parser')
            
            # 提取标题
            title = soup.title.string if soup.title else "无标题"
            logger.info(f"提取的标题: {title}")
            
            # 尝试提取正文
            content = soup.find('div', class_='article-content')
            if not content:
                content = soup.find('div', id='article-content')
            if not content:
                content = soup.find('div', id='main-content')
            if not content:
                content = soup.find('article')
            
            if content:
                content_text = content.get_text(strip=True)
                logger.info(f"成功提取正文，长度: {len(content_text)}")
            else:
                content_text = "无法提取正文"
                logger.warning("无法找到正文内容")
            
            logger.info(f"头条插件提取的正文预览: {content_text[:200]}...")
            
            return {
                "custom_field": "Toutiao plugin applied",
                "cookies_added": bool(site_cookies.get('toutiao')),
                "status_code": final_response.status_code,
                "headers": dict(final_response.headers),
                "final_url": final_response.url,
                "title": title,
                "content_preview": content_text[:200],
                "full_content": content_text
            }
        except requests.RequestException as e:
            logger.error(f"头条插件请求失败: {str(e)}")
            return {
                "custom_field": "Toutiao plugin error",
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
