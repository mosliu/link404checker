import requests
import logging
import importlib
import os
import random
from requests.exceptions import Timeout

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
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
        response = requests.get(url, headers=headers, timeout=10)
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

def follow_redirects(url, max_redirects=10):
    redirects = []
    for _ in range(max_redirects):
        try:
            # 随机选择一个User-Agent
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            logger.info(f"使用User-Agent: {headers['User-Agent']}")

            logger.info(f"正在发送GET请求到 {url}")
            response = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
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
