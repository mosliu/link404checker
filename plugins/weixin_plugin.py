from .base_plugin import BasePlugin
import re
import requests
from utils import logger, USER_AGENTS
import random
from bs4 import BeautifulSoup

class Plugin(BasePlugin):
    name = "weixin"

    def match(self, url):
        # 匹配形如 "@http://mp.weixin.qq.com/s?__biz=Mzg3ODYyNzkwNA==&mid=2247488679&idx=1&sn=46647b165453c00e0b0d15e3ce16f14e" 的URL
        return bool(re.match(r'^@?https?://mp\.weixin\.qq\.com/s\?.*', url))

    def process(self, response):
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Upgrade-Insecure-Requests': '1',
            }
            new_response = requests.get(response.url, headers=headers, allow_redirects=True, timeout=10)
            logger.info(f"微信插件请求响应状态码: {new_response.status_code}")
            
            soup = BeautifulSoup(new_response.text, 'html.parser')
            
            # 检查是否有内容已被删除的提示
            deleted_msg = soup.find('div', class_='weui-msg__title warn')
            if deleted_msg and "该内容已被发布者删除" in deleted_msg.text:
                logger.info("检测到内容已被删除")
                return {
                    "custom_field": "Weixin plugin applied",
                    "status_code": 404,  # 将状态码改为404
                    "headers": dict(new_response.headers),
                    "final_url": new_response.url,
                    "title": "内容已被删除",
                    "content_preview": "该内容已被发布者删除",
                    "full_content": "该内容已被发布者删除",
                    "is_deleted": True
                }
            
            # 如果内容未被删除，尝试提取文章内容
            title = soup.title.string if soup.title else "无标题"
            content = soup.find('div', id='js_content')
            if content:
                content_text = content.get_text(strip=True)
                logger.info(f"成功提取文章内容，长度: {len(content_text)}")
            else:
                content_text = "无法提取文章内容"
                logger.warning("无法找到文章内容")
            
            return {
                "custom_field": "Weixin plugin applied",
                "status_code": new_response.status_code,
                "headers": dict(new_response.headers),
                "final_url": new_response.url,
                "title": title,
                "content_preview": content_text[:200],
                "full_content": content_text,
                "is_deleted": False
            }
        except requests.RequestException as e:
            logger.error(f"微信插件请求失败: {str(e)}")
            return {
                "custom_field": "Weixin plugin error",
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
