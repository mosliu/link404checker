import threading
import time
from utils import get_site_cookies, logger
from plugins.toutiao_plugin import toutiao_plugin

async def run_cron():
    while True:
        for site_name, url in [('toutiao', 'https://www.toutiao.com')]:
            get_site_cookies(site_name, url)
        time.sleep(30 * 60)  # 每30分钟更新一次
    try:
        print("run_cron")
        # ... 现有代码 ...
    except Exception as e:
        # 处理异常,但不要在这里返回或退出
        print(f"发生错误: {e}")
    finally:
        await toutiao_plugin.close()

def start_cookie_update_thread():
    thread = threading.Thread(target=update_site_cookies)
    thread.daemon = True
    thread.start()
    logger.info("Cookie 更新线程已启动")
