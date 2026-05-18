<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'
import { RouterLink } from 'vue-router'

const authStore = useAuthStore()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')

const handleRegister = async () => {
  error.value = ''
  const u = username.value.trim()
  const p = password.value
  if (!u || !p || !confirmPassword.value) {
    error.value = '请填写所有字段'
    return
  }
  if (u.length < 3 || u.length > 32) {
    error.value = '用户名长度需为 3-32'
    return
  }
  if (p.length < 6) {
    error.value = '密码长度至少 6 位'
    return
  }
  if (p !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  await authStore.register(u, p)
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-muted/40 p-4">
    <div class="w-full max-w-md bg-card border border-border rounded-xl shadow-sm p-8 space-y-6 animate-slide-up">
      <div class="space-y-2 text-center">
        <h1 class="text-3xl font-bold tracking-tight">创建账户</h1>
        <p class="text-muted-foreground">注册以开始使用智能问答服务</p>
      </div>

      <div class="space-y-4">
        <div class="space-y-2">
          <label class="text-sm font-medium">用户名</label>
          <input
            v-model="username"
            type="text"
            class="w-full h-10 px-3 rounded-md border border-input bg-background ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="请输入用户名"
          />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-medium">密码</label>
          <input
            v-model="password"
            type="password"
            class="w-full h-10 px-3 rounded-md border border-input bg-background ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="请输入密码"
          />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-medium">确认密码</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="w-full h-10 px-3 rounded-md border border-input bg-background ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="请再次输入密码"
            @keyup.enter="handleRegister"
          />
        </div>
      </div>

      <div v-if="error || authStore.error" class="text-sm text-destructive text-center">
        {{ error || authStore.error }}
      </div>

      <Button class="w-full" :disabled="authStore.isLoading" @click="handleRegister">
        <span v-if="authStore.isLoading">注册中...</span>
        <span v-else>注册</span>
      </Button>

      <div class="text-center text-sm text-muted-foreground">
        已有账户？
        <RouterLink to="/login" class="text-primary hover:underline">立即登录</RouterLink>
      </div>
    </div>
  </div>
</template>
