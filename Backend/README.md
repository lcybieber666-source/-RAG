# Backend - FastAPI 问答系统后端

这是一个基于 FastAPI 的模块化后端项目，参考自根目录的 `app.py` 文件重构而成。

## 项目结构

```
Backend/
├── main.py                 # 主入口文件
├── requirements.txt        # 依赖文件
├── static/                 # 静态文件目录
└── app/
    ├── __init__.py        # 应用工厂
    ├── core/              # 核心模块
    │   ├── __init__.py
    │   ├── config.py      # 配置管理
    │   └── greeting.py    # 问候语处理
    ├── schemas/           # 数据模型
    │   ├── __init__.py
    │   └── query.py       # 请求/响应模型
    ├── routers/           # 路由模块
    │   ├── __init__.py
    │   ├── session.py     # 会话管理
    │   ├── query.py       # 问答查询
    │   ├── history.py     # 历史记录
    │   └── health.py      # 健康检查
    └── services/          # 服务层
        ├── __init__.py
        └── qa_service.py  # 问答系统服务
```

## 快速开始

### 1. 安装依赖

```bash
cd Backend
pip install -r requirements.txt
```

### 2. 运行服务

```bash
python main.py
```

服务将在 `http://127.0.0.1:8080` 启动。

## Docker 部署

项目根目录新增了一套完整的 `docker-compose` 方案，可同时启动：

- `MySQL`
- `Redis`
- `Milvus`（含 `etcd` 和 `minio`）
- `bootstrap` 初始化任务
- `FastAPI` 后端

启动前可以先复制环境样例：

```bash
copy docker\.env.example .env
```

然后在项目根目录执行：

```bash
docker compose up --build -d
```

查看后端健康状态：

```bash
docker compose ps
curl http://127.0.0.1:8080/health
```

首次启动时，`bootstrap` 服务会自动完成：

- FAQ CSV 导入 MySQL
- RAG 文档写入 Milvus

## API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/create_session` | 创建新会话 |
| POST | `/api/query` | 非流式查询 |
| WS | `/api/stream` | WebSocket 流式查询 |
| GET | `/api/history/{session_id}` | 获取历史记录 |
| DELETE | `/api/history/{session_id}` | 清除历史记录 |
| GET | `/health` | 健康检查 |
| GET | `/api/sources` | 获取学科类别 |

## 说明

- 服务层 (`qa_service.py`) 支持两种模式：
  - **真实模式**: 自动导入 `new_main.py` 中的 `IntegratedQASystem`
  - **模拟模式**: 当无法导入时，使用模拟实现进行测试
