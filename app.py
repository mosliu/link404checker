from flask import Flask
from route import check_url_blueprint
from utils import load_plugins, logger, start_cookie_update_thread

app = Flask(__name__)

# 注册蓝图
app.register_blueprint(check_url_blueprint)

if __name__ == '__main__':
    load_plugins()
    start_cookie_update_thread()
    logger.info("启动应用程序")
    app.run(debug=True)
    # app.run()
