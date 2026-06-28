# Bili23 Downloader — API Server

> **[English](README.md)**

将 [Bili23-Downloader](https://github.com/ScottSloan/Bili23-Downloader) 的下载链接解析能力暴露为 REST API——无需 GUI、无需浏览器、无需 PySide6。


```bash
cd api-server && uv sync && uv run python -m serve
# → http://127.0.0.1:8000
```

## 环境要求

- Python 3.10.x
- `uv`（包管理器，[安装](https://docs.astral.sh/uv/#installation)）

## 快速启动

```bash
git clone https://github.com/ScottSloan/Bili23-Downloader.git
cd Bili23-Downloader/api-server
uv sync                # 安装依赖（约 20 个包，无 Qt）
uv run python -m serve # 启动，监听 http://127.0.0.1:8000
```

## 接口

所有接口的交互式文档位于 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)（Swagger UI）。

| 接口 | 说明 |
|---|---|
| `GET /api/health` | 健康检查 |
| `GET /api/info?bvid=xxx` | 视频元数据（title, cid, 作者, 分P, 时长） |
| `GET /api/download?bvid=xxx` | 自动获取 cid，返回所有分P的下载链接 |
| `GET /api/parse?bvid=xxx&cid=xxx` | 精确指定剧集，返回单集下载链接 |
| `POST /api/cookies` | 注入 Bilibili 登录态 Cookie，返回 `session_id` |

### 使用示例

```bash
# 查视频信息
curl -s "http://127.0.0.1:8000/api/info?bvid=BV1E3411C7HM"

# 下载（自动取 cid）
curl -s "http://127.0.0.1:8000/api/download?bvid=BV1E3411C7HM"

# 精确指定 cid 下载
curl -s "http://127.0.0.1:8000/api/parse?bvid=BV1E3411C7HM&cid=423747920"
```

### 登录（可选）

限制级内容需要传入 B 站登录 Cookie：

```bash
# 创建 session
SID=$(curl -s -X POST http://127.0.0.1:8000/api/cookies \
  -d "SESSDATA=abc&bili_jct=def&DedeUserID=123")

# 后续请求带上 session_id
curl -s "http://127.0.0.1:8000/api/download?bvid=BVxxx&session_id=$SID"
```

Session 10 分钟过期。

## 架构

```
┌─────────────┐   import      ┌──────────────┐
│  serve.py   │──────────────▶│  worker.py   │
│  (入口)     │               │  (wrapper)   │
└──────┬──────┘               └──────┬───────┘
       │                            │
       │ routes.py                  │ from util.*
       │ session.py                 ▼
       │                     ┌──────────────┐
       │                     │ Bili23-      │
       │                     │ Downloader   │
       │                     │ src/         │
       │                     └──────────────┘
       │
       ▼
┌──────────────┐   拦截
│  stubs/      │── PySide6 / qfluentwidgets
│  (导入钩子)  │   的 import 请求
└──────────────┘
```

**直接复用父项目的代码**——服务端没有复制或重写任何下载逻辑。`VideoInfoParser`、`AudioInfoParser`、`QueryWorker`、`SyncNetWorkRequest`、`ParserBase` 全部来自原项目。

**零 GUI 依赖**——PySide6 和 qfluentwidgets 在 import 时通过 `sys.modules` 钩子拦截替换为桩模块。服务器只依赖 `httpx`、`fastapi`、`uvicorn`、`psutil`（约 20 个包）。

## 开发

```bash
uv sync --group dev  # 安装 flake8, autopep8
uv run flake8        # 代码检查
uv run autopep8 --aggressive --in-place *.py stubs/*.py
```

## 许可

GPL-3.0——与父项目 [Bili23-Downloader](https://github.com/ScottSloan/Bili23-Downloader) 一致。
