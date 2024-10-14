from .base_plugin import BasePlugin

class Plugin(BasePlugin):
    name = "example"

    def match(self, url):
        return "example.com" in url

    def process(self, response):
        # 这里可以添加特定于example.com的处理逻辑
        return {
            "custom_field": "This is an example plugin result"
        }
