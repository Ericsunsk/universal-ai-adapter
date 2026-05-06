# Universal AI Adapter (万能 AI 中转器)

Universal AI Adapter 是一个企业级的高并发、防弹式 OpenAI 协议中转网关。它可以将**任何**采用“异步提交 -> 轮询结果”的第三方生图平台（如速创、各大原生文生图/图生图异步 API）无缝转换为标准的 **OpenAI 同步响应协议**。

你可以直接将其作为代理网关挂载到 [Feng-AI](https://github.com/Ericsunsk/Feng-AI)、One-API、New-API 或任何支持 OpenAI 格式的客户端中使用。

## 🌟 核心特性

- **100% OpenAI 协议兼容**：全面兼容 `/v1/models` (连通性检测), `/v1/images/generations` (文生图), `/v1/images/edits` (局部重绘、垫图扩图)。
- **黑盒二进制流转换**：内置强大的 `multipart/form-data` 解析引擎，自动截获客户端发来的二进制参考图/蒙版，转化为下游平台要求的 Base64 URL。
- **动态表单管理后台**：无需手搓容易出错的 JSON，系统内置了一套极致美观的 Glassmorphism 风格管理后台，所见即所得地配置每个模型的独立鉴权规则、URL 映射及参数字典。
- **高并发与防弹机制**：基于 `FastAPI` + `httpx.AsyncClient`，内置全局连接池限制以防端口耗尽，并针对上游死锁或奇葩非标报文包含强容错与 3 轮自动断点重试机制。

## 🚀 极速部署

本项目完全使用 Docker 进行容器化管理。

```bash
# 1. 克隆项目
git clone https://github.com/Ericsunsk/universal-ai-adapter.git
cd universal-ai-adapter

# 2. 编辑环境变量 (可选)
# 在 docker-compose.yml 中修改 ADMIN_PASSWORD 为你想要的后台密码

# 3. 启动
docker-compose up -d --build
```

部署完成后，在浏览器访问 `http://<您的IP>:3000` 进入管理控制台。

## ⚙️ 接入指南

### 在客户端（例如 Feng-AI）中配置：
* **接口地址 / BaseURL**: `http://<部署机器IP>:3000/v1`
* **API Key**: 填写你上游服务商给你的真实 API Key（本网关负责安全透传）。
* **模型名称**: 填写你在管理后台配置支持的模型（例如 `nanobanana2`, `gpt-image-2`）。

### 命令行测试：

**1. 检测连通性**
```bash
curl -X GET "http://127.0.0.1:3000/v1/models" \
     -H "Authorization: Bearer <随意字符串>"
```

**2. 真实生图测试**
```bash
curl -X POST "http://127.0.0.1:3000/v1/images/generations" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <你的上游真实Key>" \
     -d '{
       "model": "nanobanana2",
       "prompt": "一只可爱的赛博朋克风格布偶猫，高清晰度，电影级光影",
       "size": "1024x1024"
     }'
```

## 📂 目录结构

```text
universal-ai-adapter/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI 入口与全局生命周期
│   ├── routes.py      # OpenAI 兼容路由群 (generations, edits, models)
│   ├── adapter.py     # 核心异步适配引擎与长轮询调度
│   ├── config.py      # 带文件锁的原子化 JSON 配置管理
│   └── utils.py       # OpenAI 标准报错结构封装
├── static/
│   └── index.html     # 高颜值 Dashboard 前端面板
├── data/              # 持久化存储目录 (自动生成 config.json)
├── Dockerfile         
├── docker-compose.yml 
└── requirements.txt   
```

## 📄 License
MIT License
