<script setup lang="ts">
import { ref, computed } from 'vue'
import { Send } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'

const emit = defineEmits(['send'])
const props = defineProps<{ isLoading: boolean }>()

const message = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const canSend = computed(() => message.value.trim().length > 0 && !props.isLoading)

const adjustHeight = () => {
  const el = textareaRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

const handleSend = () => {
  if (!canSend.value) return
  emit('send', message.value)
  message.value = ''
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}
</script>

<template>
  <div class="w-full max-w-4xl mx-auto p-4">
    <div 
      class="relative flex items-end gap-2 bg-background border border-input rounded-xl shadow-sm p-2 transition-all duration-300 ease-out focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50 focus-within:shadow-md"
    >
      <textarea
        ref="textareaRef"
        v-model="message"
        rows="1"
        class="flex-1 bg-transparent border-0 focus:ring-0 resize-none py-3 max-h-[200px] min-h-[44px] scrollbar-hide outline-none text-sm placeholder:text-muted-foreground/60 transition-all ml-2"
        placeholder="输入消息..."
        @input="adjustHeight"
        @keydown="handleKeydown"
      ></textarea>

      <Button
        :disabled="!canSend"
        size="icon"
        class="h-10 w-10 shrink-0 mb-[1px] transition-all duration-200"
        :class="canSend ? 'bg-primary text-primary-foreground hover:bg-primary/90 scale-100' : 'bg-muted text-muted-foreground scale-95 opacity-50'"
        @click="handleSend"
      >
        <Send class="h-4 w-4" />
      </Button>
    </div>
    <div class="text-center text-xs text-muted-foreground mt-2 opacity-80">
      AI可能会犯错，请核对重要信息。
    </div>
  </div>
</template>
