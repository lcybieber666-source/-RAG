<script setup lang="ts">
import { useSettingsStore } from '@/stores/settings'
import { storeToRefs } from 'pinia'
import Switch from '@/components/ui/Switch.vue'
import { Moon, Sun, Monitor, Type } from 'lucide-vue-next'

const settingsStore = useSettingsStore()
const { theme, responseLength } = storeToRefs(settingsStore)

const toggleTheme = () => {
  settingsStore.toggleTheme()
}
</script>

<template>
  <div class="h-full overflow-y-auto bg-background p-6 md:p-10">
    <div class="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">设置</h1>
        <p class="text-muted-foreground">管理应用偏好和AI配置。</p>
      </div>

      <div class="space-y-6">
        <!-- Appearance -->
        <div class="space-y-4 animate-slide-up" style="animation-delay: 100ms">
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <Monitor class="h-5 w-5" />
            外观
          </h2>
          <div class="rounded-lg border border-border p-4 bg-card transition-all hover:shadow-md">
            <div class="flex items-center justify-between">
              <div class="space-y-0.5">
                <div class="font-medium">深色模式</div>
                <div class="text-sm text-muted-foreground">在明亮和深色主题之间切换。</div>
              </div>
              <Switch :model-value="theme === 'dark'" @update:model-value="toggleTheme" />
            </div>
          </div>
        </div>



        <!-- Response Preference -->
        <div class="space-y-4 animate-slide-up" style="animation-delay: 200ms">
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <Type class="h-5 w-5" />
            回答偏好
          </h2>
          <div class="rounded-lg border border-border p-4 bg-card transition-all hover:shadow-md">
             <div class="space-y-2">
              <label class="text-sm font-medium">回答长度</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="len in ['brief', 'standard', 'detailed']"
                  :key="len"
                  class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 h-9 px-3 capitalize border backdrop-blur-md"
                  :class="responseLength === len ? 'bg-primary/80 text-primary-foreground border-primary/50 shadow-sm' : 'bg-background/40 hover:bg-accent/40 hover:backdrop-blur-md hover:text-accent-foreground border-input/50'"
                  @click="responseLength = len as any"
                >
                  {{ len === 'brief' ? '简洁' : len === 'standard' ? '标准' : '详细' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
