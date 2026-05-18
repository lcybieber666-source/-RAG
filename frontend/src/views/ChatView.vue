<script setup lang="ts">
import { useChatStore } from '@/stores/chat'
import { useHistoryStore } from '@/stores/history'
import { storeToRefs } from 'pinia'
import MessageList from '@/components/chat/MessageList.vue'
import InputBar from '@/components/chat/InputBar.vue'
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { API_ENDPOINTS } from '@/config/api'

const chatStore = useChatStore()
const historyStore = useHistoryStore()
const route = useRoute()
const { messages, isLoading } = storeToRefs(chatStore)

const handleSend = async (content: string) => {
  await chatStore.sendMessage(content)
}

// Watch route to load chat if ID changes
watch(() => route.params.id, async (newId, oldId) => {
    if (newId) {
        // 清除之前的消息
        chatStore.clearMessages()
        // 设置当前聊天 ID，用于后续继续对话
        chatStore.currentChatId = newId as string
        
        // Fetch history from backend
        try {
            chatStore.isLoading = true
            const res = await axios.get(API_ENDPOINTS.history(newId as string))
            if (res.data.history && res.data.history.length > 0) {
                const historyMessages: any[] = []
                // Backend returns [{question: string, answer: string}] ordered by time asc
                
                res.data.history.forEach((item: any, index: number) => {
                    historyMessages.push({
                        id: `hist-${newId}-${index}-q`,
                        role: 'user',
                        content: item.question,
                        timestamp: Date.now() - (res.data.history.length - index) * 1000
                    })
                    historyMessages.push({
                        id: `hist-${newId}-${index}-a`,
                        role: 'assistant',
                        content: item.answer,
                        timestamp: Date.now() - (res.data.history.length - index) * 1000 + 500
                    })
                })
                chatStore.messages = historyMessages
            }
        } catch (e) {
            console.error('Failed to load history', e)
        } finally {
            chatStore.isLoading = false
        }
    } else {
        // 新对话：清空消息和当前聊天 ID
        chatStore.clearMessages()
        chatStore.currentChatId = null
    }
}, { immediate: true })

</script>

<template>
  <div class="h-full flex flex-col bg-background">
    <MessageList :messages="messages" :is-loading="isLoading" />
    <div class="border-t border-border bg-background/50 backdrop-blur supports-[backdrop-filter]:bg-background/50 animate-slide-up">
      <InputBar :is-loading="isLoading" @send="handleSend" />
    </div>
  </div>
</template>
