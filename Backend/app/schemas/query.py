# 查询相关数据模型
from typing import Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str  # 查询内容，必填
    source_filter: Optional[str] = None  # 学科过滤，可选
    session_id: Optional[str] = None  # 会话 ID，可选


class QueryResponse(BaseModel):
    """查询响应模型"""
    answer: str  # 答案内容
    is_streaming: bool  # 是否流式响应
    session_id: str  # 会话 ID
    processing_time: float  # 处理时间
