import threading
import time
from utils import get_site_cookies, logger

def update_site_cookies():
    while True:
        for site_name, url in [('toutiao', 'https://www.toutiao.com')]:
            get_site_cookies(site_name, url)
        time.sleep(30 * 60)  # 每30分钟更新一次

def start_cookie_update_thread():
    thread = threading.Thread(target=update_site_cookies)
    thread.daemon = True
    thread.start()
    logger.info("Cookie 更新线程已启动")
