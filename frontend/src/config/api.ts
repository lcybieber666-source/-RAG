// API 配置文件
// 集中管理后端 API 地址

const runtimeHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const runtimeProtocol = typeof window !== 'undefined' ? window.location.protocol : 'http:'
const httpProtocol = runtimeProtocol === 'https:' ? 'https' : 'http'
const wsProtocol = runtimeProtocol === 'https:' ? 'wss' : 'ws'

// 后端服务地址
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `${httpProtocol}://${runtimeHost}:8080`

// WebSocket 地址
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || `${wsProtocol}://${runtimeHost}:8080`

// API 端点
export const API_ENDPOINTS = {
    // 会话
    createSession: `${API_BASE_URL}/api/create_session`,

    // 查询
    query: `${API_BASE_URL}/api/query`,
    stream: `${WS_BASE_URL}/api/stream`,

    // 历史记录
    history: (sessionId: string) => `${API_BASE_URL}/api/history/${sessionId}`,

    // 健康检查
    health: `${API_BASE_URL}/health`,

    // 学科类别
    sources: `${API_BASE_URL}/api/sources`,

    // 认证
    auth: {
        login: `${API_BASE_URL}/api/auth/login`,
        register: `${API_BASE_URL}/api/auth/register`,
        me: `${API_BASE_URL}/api/auth/me`,
    }
}
