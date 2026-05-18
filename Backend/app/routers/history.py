# 历史记录管理路由
from fastapi import APIRouter, HTTPException
from Backend.app.services.qa_service import qa_service

router = APIRouter()


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """查询历史消息接口"""
    try:
        history = qa_service.get_session_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清除历史消息接口"""
    success = qa_service.clear_session_history(session_id)
    if success:
        return {"status": "success", "message": "历史记录已清除"}
    else:
        raise HTTPException(status_code=500, detail="清除历史记录失败")
