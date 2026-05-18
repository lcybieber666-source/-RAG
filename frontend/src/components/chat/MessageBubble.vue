<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'
import { cn } from '@/lib/utils'
import { User, Bot, Copy, RefreshCw, ThumbsUp, ThumbsDown } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'

interface Props {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

const props = defineProps<Props>()

const formattedTime = computed(() => {
  return new Date(props.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
})

const htmlContent = computed(() => {
  return renderMarkdown(props.content)
})

const copyToClipboard = () => {
  navigator.clipboard.writeText(props.content)
}
</script>

<template>
  <div :class="cn('flex w-full mb-6 group/message', role === 'user' ? 'justify-end' : 'justify-start')">
    <div :class="cn('flex max-w-[85%] md:max-w-[75%] gap-4', role === 'user' ? 'flex-row-reverse' : 'flex-row')">
      <!-- Avatar -->
      <div
        :class="cn(
          'h-8 w-8 rounded-xl flex items-center justify-center shrink-0 shadow-sm ring-1 ring-inset',
          role === 'user' 
            ? 'bg-primary text-primary-foreground ring-primary/20' 
            : 'bg-gradient-to-br from-secondary to-secondary/80 text-secondary-foreground ring-secondary/20'
        )"
      >
        <User v-if="role === 'user'" class="h-5 w-5" />
        <Bot v-else class="h-5 w-5" />
      </div>

      <!-- Message Content -->
      <div class="flex flex-col gap-1 min-w-0">
        <div class="flex items-center gap-2 mb-1" :class="role === 'user' ? 'flex-row-reverse' : 'flex-row'">
            <span class="text-xs font-medium text-muted-foreground/80">{{ role === 'user' ? '你' : '智能助手' }}</span>
            <span class="text-[10px] text-muted-foreground/50 tabular-nums">{{ formattedTime }}</span>
        </div>

        <div
          :class="cn(
            'rounded-2xl p-4 text-sm shadow-sm overflow-hidden prose dark:prose-invert max-w-none break-words leading-relaxed transition-all duration-300 select-text cursor-text',
            role === 'user'
              ? 'bg-primary text-primary-foreground prose-headings:text-primary-foreground prose-p:text-primary-foreground prose-strong:text-primary-foreground prose-code:text-primary-foreground rounded-tr-sm shadow-primary/10'
              : 'bg-card/80 backdrop-blur-sm text-card-foreground border border-border/50 rounded-tl-sm shadow-black/5'
          )"
        >
          <!-- Using v-html for markdown content. Ensure content is sanitized if coming from untrusted sources (though markdown-it handles basic XSS) -->
          <div v-html="htmlContent" class="markdown-body"></div>
        </div>

        <!-- Actions (Assistant only) -->
        <div v-if="role === 'assistant'" class="flex items-center gap-1 mt-1 opacity-0 group-hover/message:opacity-100 transition-opacity duration-300">
          <Button variant="ghost" size="icon" class="h-7 w-7 rounded-lg hover:bg-background/80 hover:backdrop-blur-sm text-muted-foreground hover:text-foreground" @click="copyToClipboard">
            <Copy class="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="icon" class="h-7 w-7 rounded-lg hover:bg-background/80 hover:backdrop-blur-sm text-muted-foreground hover:text-foreground">
            <RefreshCw class="h-3.5 w-3.5" />
          </Button>
          <div class="flex-1"></div>
          <Button variant="ghost" size="icon" class="h-7 w-7 rounded-lg hover:bg-background/80 hover:backdrop-blur-sm text-muted-foreground hover:text-foreground">
            <ThumbsUp class="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="icon" class="h-7 w-7 rounded-lg hover:bg-background/80 hover:backdrop-blur-sm text-muted-foreground hover:text-foreground">
            <ThumbsDown class="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* Additional styles for markdown content if needed */
.markdown-body pre {
  background-color: #1e1e1e;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
}
.markdown-body code {
  font-family: monospace;
}
</style>
