import requests
import logging
import importlib
import os
import random
from requests.exceptions import Timeout
import json
from config import USE_PROXY, PROXY_URL, PROXY_TIMEOUT

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]

# 加载插件
plugins = {}

# 网站cookie缓存
site_cookies = {}

def load_plugins():
    plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
    for filename in os.listdir(plugin_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            module = importlib.import_module(f'plugins.{module_name}')
            if hasattr(module, 'Plugin'):
                plugin = module.Plugin()
                plugins[plugin.name] = plugin
                logger.info(f"加载插件: {plugin.name}")

def get_site_cookies(site_name, url):
    global site_cookies
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.cookies:
            site_cookies[site_name] = response.cookies
            logger.info(f"成功获取{site_name}的cookie: {dict(response.cookies)}")
        else:
            logger.warning(f"获取{site_name}的cookie成功，但cookie为空")
            site_cookies[site_name] = None

        # 打印响应头，以便调试
        logger.info(f"响应头: {dict(response.headers)}")
    except Exception as e:
        logger.error(f"获取{site_name}的cookie失败: {str(e)}")
        site_cookies[site_name] = None

def get_proxy():
    try:
        response = requests.get(PROXY_URL, timeout=PROXY_TIMEOUT)
        if response.status_code == 200:
            proxy_data = response.json()
            logger.info(f"获取代理: {proxy_data['proxy']}")
            return f"http://{proxy_data['proxy']}"
    except Exception as e:
        logger.error(f"获取代理失败: {str(e)}")
    return None

def make_request(url, method='GET', headers=None, allow_redirects=True, timeout=15):
    proxy = get_proxy() if USE_PROXY else None
    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            allow_redirects=allow_redirects,
            timeout=timeout,
            proxies={'http': proxy, 'https': proxy} if proxy else None
        )
        return response
    except Exception as e:
        logger.error(f"请求失败: {str(e)}")
        raise

def follow_redirects(url, max_redirects=10):
    redirects = []
    plugin_result = {}
    for _ in range(max_redirects):
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            logger.info(f"使用User-Agent: {headers['User-Agent']}")

            logger.info(f"正在发送GET请求到 {url}")
            response = make_request(url, headers=headers, allow_redirects=False)
            logger.info(f"收到响应，状态码: {response.status_code}")
            logger.info(f"响应头: {dict(response.headers)}")

            content_preview = response.text[:100] if response.text else "无内容"
            logger.info(f"响应内容预览: {content_preview}")

            redirect_info = {
                "url": url,
                "status_code": response.status_code,
                "reason": response.reason,
                "user_agent": headers['User-Agent']
            }

            # 使用插件进行匹配
            for plugin in plugins.values():
                if plugin.match(url):
                    plugin_result = plugin.process(response)
                    redirect_info.update(plugin_result)
                    # 如果插件返回了新的响应，使用新的响应进行后续处理
                    if 'new_status_code' in plugin_result:
                        response = requests.Response()
                        response.status_code = plugin_result['new_status_code']
                        response.headers = plugin_result['new_headers']
                        response.url = url
                    # 处理插件返回的结果
                    if plugin_result.get('stop_redirect', False):
                        logger.info("插件要求停止重定向")
                        redirects.append(redirect_info)
                        return redirects
                    break
            redirects.append(redirect_info)
            if response.status_code == 404 or plugin_result.get('status_code') == 404:
                logger.info("遇到404 Not Found，停止跟踪")
                
                return redirects
            elif response.is_redirect:
                new_url = response.headers.get('Location')
                logger.info(f"检测到重定向: {response.status_code} {response.reason}")
                logger.info(f"重定向位置: {new_url}")
                url = new_url if new_url.startswith('http') else f"{response.url.rstrip('/')}/{new_url.lstrip('/')}"
            else:
                break
        except Timeout:
            logger.error("请求超时")
            redirects.append({
                "url": url,
                "error": "Request timeout"
            })
            break
        except requests.RequestException as e:
            logger.error(f"请求发生错误: {str(e)}")
            redirects.append({
                "url": url,
                "error": str(e)
            })
            break
    return redirects
