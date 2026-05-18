import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Conversation {
  id: string
  title: string
  lastMessage: string
  timestamp: number
}

export const useHistoryStore = defineStore('history', () => {
  const conversations = ref<Conversation[]>([])

  // Load from local storage
  const loadConversations = () => {
    const stored = localStorage.getItem('conversations')
    if (stored) {
      conversations.value = JSON.parse(stored)
      // Sort by timestamp desc
      conversations.value.sort((a, b) => b.timestamp - a.timestamp)
    }
  }

  const addConversation = (conv: Conversation) => {
    const existingIndex = conversations.value.findIndex(c => c.id === conv.id)
    if (existingIndex > -1) {
        // Update existing
        conversations.value[existingIndex] = { ...conversations.value[existingIndex], ...conv }
    } else {
        // Add new
        conversations.value.unshift(conv)
    }
    // Re-sort
    conversations.value.sort((a, b) => b.timestamp - a.timestamp)
    save()
  }

  const deleteConversation = (id: string) => {
    conversations.value = conversations.value.filter(c => c.id !== id)
    save()
  }

  const save = () => {
    localStorage.setItem('conversations', JSON.stringify(conversations.value))
  }

  // Initial load
  loadConversations()

  return {
    conversations,
    addConversation,
    deleteConversation,
    loadConversations
  }
})
