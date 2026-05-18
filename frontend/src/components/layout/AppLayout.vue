<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import { ref } from 'vue'
import { Menu } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'

const isSidebarOpen = ref(false)
</script>

<template>
  <div class="flex h-screen w-full bg-background">
    <!-- Sidebar (Desktop) -->
    <aside class="hidden md:flex w-64 flex-col fixed inset-y-0 z-50">
      <AppSidebar />
    </aside>

    <!-- Sidebar (Mobile) -->
    <Transition name="fade">
      <div v-if="isSidebarOpen" class="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm md:hidden" @click="isSidebarOpen = false" />
    </Transition>
    <aside
      class="fixed inset-y-0 left-0 z-50 w-64 bg-background/80 backdrop-blur-md border-r transition-transform duration-300 md:hidden"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <AppSidebar />
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col h-full md:pl-64 transition-all duration-300">
      <!-- Mobile Header -->
      <header class="md:hidden p-4 border-b flex items-center justify-between bg-background">
        <Button variant="ghost" size="icon" @click="isSidebarOpen = !isSidebarOpen">
          <Menu class="h-5 w-5" />
        </Button>
        <span class="font-semibold">Vue QnA</span>
        <div class="w-9"></div> <!-- Spacer -->
      </header>

      <div class="flex-1 overflow-hidden relative">
        <slot />
      </div>
    </main>
  </div>
</template>
