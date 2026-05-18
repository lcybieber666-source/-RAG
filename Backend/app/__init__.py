# FastAPI 应用工厂模块
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from Backend.app.routers import session, query, history, health, auth
from Backend.app.core.config import settings
from Backend.app.db.users import init_users_table


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例"""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_users_table()
        yield

    # 创建 FastAPI 应用实例
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    
    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 创建静态文件目录
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    os.makedirs(static_dir, exist_ok=True)
    
    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # 注册路由
    app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
    app.include_router(session.router, prefix="/api", tags=["会话管理"])
    app.include_router(query.router, prefix="/api", tags=["问答查询"])
    app.include_router(history.router, prefix="/api", tags=["历史记录"])
    app.include_router(health.router, tags=["健康检查"])
    
    return app
