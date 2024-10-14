from flask import Blueprint, request, jsonify
from utils import logger, follow_redirects

check_url_blueprint = Blueprint('check_url', __name__)

@check_url_blueprint.route('/check_url', methods=['POST'])
def check_url():
    data = request.json
    url = data.get('url')
    
    logger.info(f"收到请求检查URL: {url}")
    logger.info(f"请求头: {request.headers}")
    logger.info(f"请求体: {request.data}")
    
    if not url:
        logger.warning("没有提供URL")
        return jsonify({"error": "No URL provided"}), 400
    
    redirects = follow_redirects(url)
    
    result = {
        "redirects": redirects,
        "final_status": redirects[-1]["status_code"] if "status_code" in redirects[-1] else "Error",
        "final_url": redirects[-1]["url"]
    }
    
    return jsonify(result), 200
