import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useHistoryStore } from './history'
import { API_ENDPOINTS } from '@/config/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const currentChatId = ref<string | null>(null)
  let socket: WebSocket | null = null
  let shouldStop = false

  const stopGeneration = () => {
    shouldStop = true
    isLoading.value = false
    // 关闭当前 WebSocket 连接以停止接收
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close()
      socket = null
    }
    // 在最后一条消息末尾添加提示
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content) {
      lastMsg.content += '\n\n*[生成已停止]*'
    }
  }

  const addMessage = (message: Message) => {
    messages.value.push(message)
  }

  const clearMessages = () => {
    messages.value = []
  }

  const connectWebSocket = () => {
    if (socket && socket.readyState === WebSocket.OPEN) return

    socket = new WebSocket(API_ENDPOINTS.stream)

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      const historyStore = useHistoryStore()

      if (data.type === 'start') {
        // Start of a new message stream
        // Backend might confirm session_id
        if (!currentChatId.value && data.session_id) {
          currentChatId.value = data.session_id
        }
        addMessage({
          id: Date.now().toString(),
          role: 'assistant',
          content: '',
          timestamp: Date.now()
        })
      } else if (data.type === 'token') {
        // Append token to the last assistant message
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          lastMsg.content += data.token
        }
      } else if (data.type === 'end') {
        isLoading.value = false
        // Update history last message
        if (currentChatId.value) {
          const lastMsg = messages.value[messages.value.length - 1]
          historyStore.addConversation({
            id: currentChatId.value,
            title: messages.value[0]?.content.substring(0, 30) || 'New Chat',
            lastMessage: lastMsg.content,
            timestamp: Date.now()
          })
        }
      } else if (data.type === 'error') {
        console.error('WebSocket error:', data.error)
        isLoading.value = false
        addMessage({
          id: Date.now().toString(),
          role: 'assistant',
          content: `Error: ${data.error}`,
          timestamp: Date.now()
        })
      }
    }

    socket.onclose = () => {
      console.log('WebSocket disconnected')
    }

    socket.onerror = (error) => {
      console.error('WebSocket connection error:', error)
      isLoading.value = false
    }
  }

  const sendMessage = async (content: string) => {
    if (!content.trim()) return

    isLoading.value = true
    const historyStore = useHistoryStore()

    // Ensure session ID
    if (!currentChatId.value) {
      currentChatId.value = generateUUID()
      // Create initial history entry
      historyStore.addConversation({
        id: currentChatId.value,
        title: content.substring(0, 30) + (content.length > 30 ? '...' : ''),
        lastMessage: content,
        timestamp: Date.now()
      })
    }

    // Ensure connection
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      connectWebSocket()
      // Wait for connection
      await new Promise<void>((resolve) => {
        if (!socket) return
        if (socket.readyState === WebSocket.OPEN) resolve()
        socket.onopen = () => resolve()
      })
    }

    // Add user message immediately
    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: Date.now()
    })

    // Send to backend
    socket?.send(JSON.stringify({
      query: content,
      session_id: currentChatId.value
    }))
  }

  return {
    messages,
    isLoading,
    currentChatId,
    addMessage,
    clearMessages,
    sendMessage,
    stopGeneration
  }
})
