<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useHistoryStore } from '@/stores/history'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import { Plus, MessageSquare, Settings, Moon, Sun, Trash2, LogOut } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { cn } from '@/lib/utils'

const router = useRouter()
const chatStore = useChatStore()
const historyStore = useHistoryStore()
const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const conversations = computed(() => historyStore.conversations)
const isDark = computed(() => settingsStore.theme === 'dark')

const startNewChat = () => {
  chatStore.clearMessages()
  chatStore.currentChatId = null
  router.push('/')
}

const openChat = (id: string) => {
  chatStore.currentChatId = id
  // Load chat messages (mock logic: ideally load from backend/store)
  router.push(`/chat/${id}`)
}

const deleteChat = (e: Event, id: string) => {
  e.stopPropagation()
  historyStore.deleteConversation(id)
  if (chatStore.currentChatId === id) {
    startNewChat()
  }
}

const toggleTheme = () => {
  settingsStore.toggleTheme()
}

const handleLogout = () => {
  authStore.logout()
}
</script>

<template>
  <div class="flex flex-col h-full bg-muted/40 border-r border-border transition-colors duration-300">
    <div class="p-4">
      <Button class="w-full justify-start gap-2 shadow-sm hover:shadow-md transition-all duration-300" @click="startNewChat">
        <Plus class="h-4 w-4" />
        新建对话
      </Button>
    </div>

    <div class="flex-1 overflow-y-auto px-2 py-2">
      <Transition name="fade" mode="out-in">
        <div v-if="conversations.length === 0" class="text-center text-sm text-muted-foreground py-4">
          暂无历史
        </div>
        <div v-else class="space-y-1">
          <TransitionGroup name="message">
            <div
              v-for="chat in conversations"
              :key="chat.id"
              :class="cn(
                'group flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium cursor-pointer transition-all duration-200 ease-in-out',
                chatStore.currentChatId === chat.id 
                  ? 'bg-accent text-accent-foreground shadow-sm translate-x-1' 
                  : 'text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground hover:translate-x-1'
              )"
              @click="openChat(chat.id)"
            >
              <div class="flex items-center gap-2 overflow-hidden">
                <MessageSquare class="h-4 w-4 shrink-0 transition-transform group-hover:scale-110" />
                <span class="truncate">{{ chat.title }}</span>
              </div>
              <button
                class="opacity-0 group-hover:opacity-100 hover:text-destructive transition-all duration-200 hover:scale-110 p-1"
                @click="(e) => deleteChat(e, chat.id)"
              >
                <Trash2 class="h-4 w-4" />
              </button>
            </div>
          </TransitionGroup>
        </div>
      </Transition>
    </div>

    <div class="p-4 border-t border-border space-y-2">
      <div v-if="authStore.user" class="px-2 py-1.5 text-sm font-medium text-muted-foreground">
        你好, {{ authStore.user.username }}
      </div>
      <Button variant="ghost" class="w-full justify-start gap-2 hover:translate-x-1 transition-transform" @click="toggleTheme">
        <component :is="isDark ? Sun : Moon" class="h-4 w-4 transition-transform hover:rotate-90" />
        {{ isDark ? '明亮模式' : '深色模式' }}
      </Button>
      <Button variant="ghost" class="w-full justify-start gap-2 hover:translate-x-1 transition-transform" @click="router.push('/settings')">
        <Settings class="h-4 w-4 transition-transform hover:rotate-90" />
        设置
      </Button>
      <Button variant="ghost" class="w-full justify-start gap-2 hover:translate-x-1 transition-transform text-destructive hover:text-destructive" @click="handleLogout">
        <LogOut class="h-4 w-4 transition-transform hover:scale-110" />
        退出登录
      </Button>
    </div>
  </div>
</template>
