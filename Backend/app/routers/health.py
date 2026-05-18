# 健康检查路由
from fastapi import APIRouter
from Backend.app.services.qa_service import qa_service
from Backend.app.services.qa_service import get_qa_system

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查接口"""
    rag_ready = True
    rag_error = None
    try:
        get_qa_system()
    except Exception as e:
        rag_ready = False
        rag_error = str(e)

    payload = {"status": "healthy", "rag_ready": rag_ready}
    if not rag_ready:
        payload["rag_error"] = rag_error
    return payload


@router.get("/api/sources")
async def get_sources():
    """获取有效学科类别接口"""
    return {"sources": qa_service.get_valid_sources()}
