# 会话管理路由
import uuid
from fastapi import APIRouter

router = APIRouter()


@router.post("/create_session")
async def create_session():
    """创建新会话接口"""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}
