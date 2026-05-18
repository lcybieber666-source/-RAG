<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'
import { RouterLink } from 'vue-router'

const authStore = useAuthStore()
const username = ref('')
const password = ref('')
const localError = ref('')

const handleLogin = async () => {
  localError.value = ''
  const u = username.value.trim()
  const p = password.value
  if (!u || !p) {
    localError.value = '请输入用户名和密码'
    return
  }
  await authStore.login(u, p)
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-muted/40 p-4">
    <div class="w-full max-w-md bg-card border border-border rounded-xl shadow-sm p-8 space-y-6 animate-slide-up">
      <div class="space-y-2 text-center">
        <h1 class="text-3xl font-bold tracking-tight">欢迎回来</h1>
        <p class="text-muted-foreground">登录您的账户以继续使用问答系统</p>
      </div>

      <div class="space-y-4">
        <div class="space-y-2">
          <label class="text-sm font-medium">用户名</label>
          <input
            v-model="username"
            type="text"
            class="w-full h-10 px-3 rounded-md border border-input bg-background ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="请输入用户名"
            @keyup.enter="handleLogin"
          />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-medium">密码</label>
          <input
            v-model="password"
            type="password"
            class="w-full h-10 px-3 rounded-md border border-input bg-background ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </div>
      </div>

      <div v-if="localError || authStore.error" class="text-sm text-destructive text-center">
        {{ localError || authStore.error }}
      </div>

      <Button class="w-full" :disabled="authStore.isLoading" @click="handleLogin">
        <span v-if="authStore.isLoading">登录中...</span>
        <span v-else>登录</span>
      </Button>

      <div class="text-center text-sm text-muted-foreground">
        还没有账户？
        <RouterLink to="/register" class="text-primary hover:underline">立即注册</RouterLink>
      </div>
    </div>
  </div>
</template>
