# URL 检查器

这是一个Flask应用程序，提供API端点来检查给定URL的响应状态，包括跟踪所有重定向直到遇到404或最终目标。它支持通过插件系统来处理不同网站的特定逻辑。

## 项目结构

```
url_checker/
│
├── app.py          # 主应用入口
├── route.py        # 路由定义
├── utils.py        # 辅助函数和全局变量
├── requirements.txt
├── README.md
└── plugins/
    ├── __init__.py
    ├── base_plugin.py
    ├── example_plugin.py
    └── toutiao_plugin.py
```

## 安装

1. 克隆此仓库
2. 创建虚拟环境（推荐）：
   ```
   python -m venv venv
   source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate
   ```
3. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

## 运行

运行以下命令启动应用：

```
python app.py
```

应用将在 `http://127.0.0.1:5000` 上运行。

## 使用

发送POST请求到 `/check_url` 端点，包含要检查的URL。例如：

```
curl -X POST -H "Content-Type: application/json" -d '{"url":"https://example.com"}' http://127.0.0.1:5000/check_url
```

## 响应

API将返回一个JSON对象，包含以下信息：

- `redirects`: 一个列表，包含所有重定向的详细信息，每个元素包括：
  - `url`: 访问的URL
  - `status_code`: HTTP状态码
  - `reason`: 状态码的文字描述
  - 其他由插件添加的自定义字段
- `final_status`: 最终的HTTP状态码
- `final_url`: 最终访问的URL

## 插件系统

要为特定网站添加自定义处理逻辑，请在`plugins`文件夹中创建新的插件文件。每个插件应该继承`BasePlugin`类并实现以下方法：

- `match(url)`: 判断是否应该使用此插件处理给定的URL
- `process(response)`: 处理响应并返回自定义结果

查看`plugins/example_plugin.py`作为示例。

### 头条插件

我们添加了一个专门用于处理头条网站的插件 `toutiao_plugin.py`。这个插件会在遇到形如 "@https://www.toutiao.com/w/1804448956217344/" 的URL时自动添加必要的cookie。插件使用缓存的cookie，如果缓存中没有cookie，会立即获取。

## 功能特点

- 跟踪URL重定向链
- 支持插件系统，可以为特定网站添加自定义处理逻辑
- 使用随机User-Agent进行请求，以模拟不同的浏览器行为
- 自动获取并缓存头条网站的cookie，每30分钟更新一次
- 总体请求超时时间设置为10秒

## 随机User-Agent

应用程序使用预定义的User-Agent列表，每次请求时随机选择一个User-Agent。这有助于模拟不同的浏览器行为，减少被目标网站识别为自动化工具的可能性。

## 日志

应用程序会记录详细的处理过程日志，包括插件的加载和使用情况。

默认情况下，日志会输出到控制台。如果您想将日志保存到文件中，请修改`app.py`中的日志配置。

## 注意

应用程序默认最多跟踪10次重定向，以防止无限循环。如果需要修改这个限制，可以在`app.py`中调整`follow_redirects`函数的`max_redirects`参数。

## 使用Docker运行

本项目支持使用Docker运行。确保您已经安装了Docker和Docker Compose，然后按照以下步骤操作：

1. 克隆此仓库
2. 在项目根目录下运行：
   ```
   docker-compose up --build
   ```
3. 应用将在 `http://localhost:5000` 上运行

要停止应用，请使用 Ctrl+C，然后运行：
```
docker-compose down
```

## Docker 镜像

本项目的 Docker 镜像已发布到 Docker Hub。您可以使用以下命令拉取最新的镜像：


## Action
为了使这个工作流程正常工作，您需要在 GitHub 仓库的 Settings > Secrets 中添加两个 secrets：
DOCKERHUB_USERNAME: 您的 Docker Hub 用户名
DOCKERHUB_TOKEN: 您的 Docker Hub 访问令牌（不是密码）