# 配置模块
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基本配置
    APP_TITLE: str = "问答系统API"
    APP_DESCRIPTION: str = "集成MySQL和RAG的智能问答系统"
    APP_VERSION: str = "1.0.0"

    # CORS 配置
    CORS_ORIGINS: List[str] = ["*"]

    # 服务器配置
    HOST: str = "0.0.0.0"  # 修改：允许外部访问
    PORT: int = 8080

    AUTH_SECRET_KEY: str = "change-me"
    AUTH_ALGORITHM: str = "HS256"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()

