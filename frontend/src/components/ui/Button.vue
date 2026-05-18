<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  variant?: 'default' | 'secondary' | 'ghost' | 'outline' | 'destructive'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'default',
  class: '',
})

const buttonClass = computed(() => {
  return cn(
    // Added: active:scale-95 for micro-interaction click effect
    'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-95',
    {
      'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm hover:shadow-md': props.variant === 'default',
      'bg-secondary text-secondary-foreground hover:bg-secondary/80 shadow-sm hover:shadow-md': props.variant === 'secondary',
      'bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-sm hover:shadow-md': props.variant === 'destructive',
      'border border-input bg-background hover:bg-accent hover:text-accent-foreground shadow-sm': props.variant === 'outline',
      'hover:bg-accent hover:text-accent-foreground': props.variant === 'ghost',
      'h-10 px-4 py-2': props.size === 'default',
      'h-9 rounded-md px-3': props.size === 'sm',
      'h-11 rounded-md px-8': props.size === 'lg',
      'h-10 w-10': props.size === 'icon',
    },
    props.class
  )
})
</script>

<template>
  <button :class="buttonClass">
    <slot />
  </button>
</template>
