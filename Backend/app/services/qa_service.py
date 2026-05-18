# 问答系统服务模块
import sys
import os
from typing import Optional, List, Tuple, Generator

# 添加项目根目录到路径，以便导入 new_main 模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

_qa_system = None
_use_mock = False
_init_error = None
_allow_mock = (os.getenv("QA_USE_MOCK") or "").lower() in {"1", "true", "yes"}


def _ensure_real_system():
    global _qa_system, _use_mock, _init_error
    if _qa_system is not None:
        return
    if _use_mock:
        return
    try:
        from new_main import IntegratedQASystem

        _qa_system = IntegratedQASystem()
    except Exception as e:
        _qa_system = None
        _init_error = str(e)
        if _allow_mock:
            _use_mock = True


class QAService:
    """问答系统服务封装类"""

    def __init__(self):
        self._qa_system = None
        self._use_mock = False
        self._mock_history = {}  # 模拟历史记录

    def _sync_state(self):
        _ensure_real_system()
        self._qa_system = _qa_system
        self._use_mock = _use_mock

    def _require_real(self):
        if self._use_mock:
            return
        if self._qa_system is None:
            raise RuntimeError(_init_error or "Real QA System is not available.")

    def get_session_history(self, session_id: str) -> List[dict]:
        """获取会话历史"""
        self._sync_state()
        if self._use_mock:
            return self._mock_history.get(session_id, [])
        self._require_real()
        return self._qa_system.get_session_history(session_id)

    def clear_session_history(self, session_id: str) -> bool:
        """清除会话历史"""
        self._sync_state()
        if self._use_mock:
            if session_id in self._mock_history:
                del self._mock_history[session_id]
            return True
        self._require_real()
        return self._qa_system.clear_session_history(session_id)

    def bm25_search(self, query: str, threshold: float = 0.85) -> Tuple[str, bool]:
        """执行 BM25 搜索"""
        self._sync_state()
        if self._use_mock:
            # 模拟实现：返回需要 RAG
            return "", True
        self._require_real()
        return self._qa_system.bm25_search.search(query, threshold=threshold)

    def query(self, query: str, source_filter: Optional[str] = None,
              session_id: Optional[str] = None) -> Generator[Tuple[str, bool], None, None]:
        """执行问答查询（生成器）"""
        self._sync_state()
        if self._use_mock:
            # 模拟流式响应
            response = f"这是对「{query}」的模拟回答。请确保已正确安装 new_main 模块以获取真实响应。"
            for char in response:
                yield char, False
            yield "", True
        else:
            self._require_real()
            for token, is_complete in self._qa_system.query(query, source_filter=source_filter, session_id=session_id):
                yield token, is_complete

    def get_valid_sources(self) -> List[str]:
        """获取有效学科类别列表"""
        self._sync_state()
        if self._use_mock:
            return ["Python", "Java", "前端", "数据库", "Linux"]
        if self._qa_system is None:
            return ["ai", "java", "test", "ops", "bigdata"]
        return self._qa_system.config.VALID_SOURCES

    def create_user(self, username: str, password: str) -> bool:
        """创建用户"""
        self._sync_state()
        if self._use_mock:
            # 在模拟模式下，总是返回成功
            # 实际生产环境中，应实现真正的用户存储机制
            return True
        self._require_real()
        return self._qa_system.create_user(username, password)

    def verify_user(self, username: str, password: str) -> bool:
        """验证用户"""
        self._sync_state()
        if self._use_mock:
            # 在模拟模式下，简单地返回成功
            # 实际生产环境中，应实现真正的用户验证机制
            return username and password  # 简单验证非空
        self._require_real()
        return self._qa_system.verify_user(username, password)


# 创建全局服务实例
qa_service = QAService()


def get_qa_system():
    """获取集成问答系统实例 (直接访问底层实例)"""
    _ensure_real_system()
    if _use_mock:
        return qa_service
    if _qa_system is None:
        raise RuntimeError(_init_error or "Real QA System is not available.")
    return _qa_system
