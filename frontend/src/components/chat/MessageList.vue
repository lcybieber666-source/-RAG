<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import type { Message } from '@/stores/chat'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{
  messages: Message[]
  isLoading?: boolean
}>()

const containerRef = ref<HTMLDivElement | null>(null)

const scrollToBottom = async () => {
  await nextTick()
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight
  }
}

watch(() => props.messages.length, scrollToBottom)
watch(() => props.isLoading, scrollToBottom)

onMounted(scrollToBottom)
</script>

<template>
  <div ref="containerRef" class="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
    <div class="max-w-4xl mx-auto">
      <Transition name="fade" mode="out-in">
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-[50vh] text-center text-muted-foreground">
          <h2 class="text-4xl font-bold mb-4 tracking-tight">欢迎使用药物配伍禁忌查询系统</h2>
          <p class="text-lg opacity-80">输入问题开始对话。</p>
        </div>
      </Transition>
      
      <TransitionGroup name="message" tag="div" class="space-y-6">
        <MessageBubble
          v-for="msg in messages"
          :key="msg.id"
          :role="msg.role"
          :content="msg.content"
          :timestamp="msg.timestamp"
        />
      </TransitionGroup>

      <Transition name="fade">
        <div v-if="isLoading" class="flex justify-start mb-6 mt-6">
          <div class="flex items-center gap-2 p-4 bg-card rounded-lg border border-border shadow-sm">
            <div class="flex gap-1">
              <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>
