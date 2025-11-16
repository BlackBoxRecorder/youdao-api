# 有道词典API服务

这是一个基于Flask的Web API服务，整合了有道词典Web API，提供单词查询功能。

## 功能特性

- 基础单词释义查询
- 音标和发音链接
- 网络释义（短语）
- 柯林斯词典例句
- 双语例句
- RESTful API接口
- SQLite缓存机制

## 技术栈

- Python 3.12+
- Flask - Web框架
- Requests - HTTP请求库
- BeautifulSoup4 - HTML解析库

## 安装依赖

项目使用 `uv` 进行依赖管理，通过 `pyproject.toml` 和 `uv.lock` 文件锁定依赖版本。

```bash
# 安装uv（如果尚未安装）
pip install uv

# 安装项目依赖
uv sync
```

## 使用Docker

项目包含Dockerfile，可以轻松打包成Docker镜像。

### 构建Docker镜像

```bash
docker build -t youdao-api .
```

### 运行Docker容器

```bash
# 前台运行
docker run -p 5088:5088 youdao-api

# 后台运行
docker run -d -p 5088:5088 --name youdao-api-container youdao-api

# 挂载本地目录以持久化数据
docker run -d -p 5088:5088 -v $(pwd)/audio:/app/audio -v $(pwd)/cache.db:/app/cache.db --name youdao-api-container youdao-api
```

### 环境变量

可以通过以下环境变量自定义服务：

- `HOST` - 服务监听的主机地址（默认: 127.0.0.1）
- `PORT` - 服务监听的端口（默认: 5088）

```bash
docker run -d -p 5088:5088 -e PORT=8080 --name youdao-api-container youdao-api
```

## 运行服务

```bash
# 默认运行（监听127.0.0.1:5088）
uv run main.py
```

## API接口

### 单词查询接口

```
GET /api/translate?word={单词}
```

**示例请求：**
```
GET /api/translate?word=hello
```

**响应示例：**
```json
{
  "success": true,
  "error": "",
  "data": {
    "word": "hello",
    "phonetic": {
      "phonetic": "həˈləʊ",
      "audio": "https://dict.youdao.com/dictvoice?type=2&audio=hello"
    },
    "explains": [
      "int. 喂；哈罗",
      "n. 表示问候， 惊奇或唤起注意时的用语",
      "interjection. hello!",
      "U. Hello!",
      "n. Hello!"
    ],
    "phrase": [
      {
        "key": "hello world",
        "value": ["你好，世界"]
      }
    ],
    "collins_sents": [
      {
        "description": "Hello is an exclamation used in English when meeting someone or to attract someone's attention.",
        "example": "Hello, Paul. How are you?",
        "translate": "你好，保罗。你好吗？"
      }
    ],
    "trans_sents": [
      {
        "audio_url": "https://dict.youdao.com/dictvoice?audio=...",
        "example": "She walked in and said hello in a quiet voice.",
        "translate": "她走进来，轻声说了句你好。"
      }
    ]
  }
}
```

### 音频文件访问接口

```
GET /api/audio/{filename}
```

**示例请求：**
```
GET /api/audio/4fb05030bab22a053611e825deeb3eb6.mp3
```

**响应：**
直接返回音频文件内容，可以用于播放或下载。

### 健康检查接口

```
GET /api/health
```

**响应示例：**
```json
{
  "status": "healthy",
  "service": "youdao-combined-api",
  "version": "1.0.0"
}
```

### 根路径信息接口

```
GET /
```

返回API服务的基本信息和可用端点说明。


## 数据库结构

数据库包含一个名为 `word_cache` 的表，包含以下字段：
- `word` (TEXT, PRIMARY KEY) - 单词
- `phonetic` (TEXT) - 音标信息（JSON字符串）
- `explains` (TEXT) - 释义信息（JSON字符串）
- `phrase` (TEXT) - 短语信息（JSON字符串）
- `collins_sents` (TEXT) - 柯林斯例句（JSON字符串）
- `trans_sents` (TEXT) - 双语例句（JSON字符串）

### 音频文件处理

为了提供更好的用户体验，服务会自动下载音频文件并保存到本地：
- 音频文件保存在项目根目录的 `audio` 文件夹中
- 数据库中保存的是音频文件的文件名而非URL
- 文件名通过URL的MD5哈希值生成，确保唯一性

## 项目结构

```
.
├── main.py          # 主程序文件，包含API实现
├── database.py      # 数据库管理模块
├── audio_manager.py # 音频文件管理模块
├── Dockerfile       # Docker镜像配置文件
├── pyproject.toml   # 项目配置和依赖声明
├── uv.lock         # 依赖锁定文件
├── cache.db        # SQLite缓存数据库
├── audio/          # 音频文件目录
└── README.md       # 项目说明文档
```

## 使用示例

启动服务后，可以通过以下方式访问API：

1. 浏览器访问: `http://localhost:5088/api/translate?word=hello`
2. curl命令:
   ```bash
   curl "http://localhost:5088/api/translate?word=hello"
   ```

## 许可证

MIT License