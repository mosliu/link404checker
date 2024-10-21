from .base_plugin import BasePlugin
import re
from utils import logger, USER_AGENTS, make_request
import random
from bs4 import BeautifulSoup

class Plugin(BasePlugin):
    name = "bilibili"

    def match(self, url):
        # 匹配形如 "@https://www.bilibili.com/video/av113277094856596/" 或其他视频ID格式的URL
        # return bool(re.match(r'^@?https?://(?:www\.)?bilibili\.com/video/[a-zA-Z0-9]+/?.*$', url))
        return bool(re.match(r'^@?https?://(?:www\.)?bilibili\.com/[a-zA-Z0-9]+/?.*$', url))

    def process(self, response):
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://www.bilibili.com/',
            }
            new_response = make_request(response.url, headers=headers, allow_redirects=True)
            logger.info(f"哔哩哔哩插件请求响应状态码: {new_response.status_code}")
            
            soup = BeautifulSoup(new_response.text, 'html.parser')
            
            # 检查是否有视频不存在的提示
            error_div = soup.find('div', class_='error-text')
            if error_div and "啊叻？视频不见了？" in error_div.text:
                logger.info("检测到视频不存在")
                return {
                    "custom_field": "Bilibili plugin applied",
                    "status_code": 404,
                    "headers": dict(new_response.headers),
                    "final_url": new_response.url,
                    "title": "视频不存在",
                    "content_preview": "啊叻？视频不见了？",
                    "full_content": "视频不存在或已被删除",
                    "is_deleted": True
                }
            
            # 如果视频存在，尝试提取视频信息
            # 修改标题提取方法
            title = soup.find('title')
            title_text = title.text.strip() if title else "无标题"
            
            description = soup.find('div', class_='desc-info-text')
            description_text = description.text.strip() if description else "无描述"
            
            content_preview = f"{title_text}\n{description_text[:200]}"
            
            return {
                "custom_field": "Bilibili plugin applied",
                "status_code": new_response.status_code,
                "headers": dict(new_response.headers),
                "final_url": new_response.url,
                "title": title_text,
                "content_preview": content_preview,
                "full_content": description_text,
                "is_deleted": False
            }
        except Exception as e:
            logger.error(f"哔哩哔哩插件请求失败: {str(e)}")
            return {
                "custom_field": "Bilibili plugin error",
                "error": str(e),
                "status_code": getattr(new_response, 'status_code', None) if 'new_response' in locals() else None
            }
