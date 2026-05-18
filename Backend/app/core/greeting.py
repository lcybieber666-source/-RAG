# 问候语处理模块
import re
from typing import Optional

# 定义日常问候用语模式和回复
GREETING_PATTERNS = [
    {
        "pattern": r"^(你好|您好|hi|hello)",
        "response": "你好，很高兴为你服务！"
    },
    {
        "pattern": r"^(你是谁|您是谁|你叫什么|who are you)",
        "response": "我是一个专注于医药配伍的RAG系统，帮助你查询医药配伍禁忌等知识"
    },
    {
        "pattern": r"^(在吗|在不在|有人吗)",
        "response": "我在！我是一个专注于医药配伍的RAG系统，随时为你解答问题！"
    },
    {
        "pattern": r"^(干嘛呢|你在干嘛|做什么)",
        "response": "我正在待命，随时为你解答相关问题！有什么我可以帮你的？"
    }
]


def check_greeting(query: str) -> Optional[str]:
    """
    检查是否为日常问候用语并返回模板回复
    
    Args:
        query: 用户查询内容
        
    Returns:
        匹配的问候回复，如果无匹配则返回 None
    """
    query_text = query.strip()
    for pattern_info in GREETING_PATTERNS:
        if re.match(pattern_info["pattern"], query_text, re.IGNORECASE):
            return pattern_info["response"]
    return None
