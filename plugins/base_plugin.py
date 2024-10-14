class BasePlugin:
    name = "base"

    def match(self, url):
        return False

    def process(self, response):
        return {}
