import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<'light' | 'dark'>(localStorage.getItem('theme') as 'light' | 'dark' || 'light')
  const responseLength = ref<'brief' | 'standard' | 'detailed'>(localStorage.getItem('responseLength') as any || 'standard')

  // Apply theme to document
  const applyTheme = (newTheme: 'light' | 'dark') => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(newTheme)
  }

  // Initial application
  applyTheme(theme.value)

  watch(theme, (newVal) => {
    localStorage.setItem('theme', newVal)
    applyTheme(newVal)
  })

  watch(responseLength, (newVal) => {
    localStorage.setItem('responseLength', newVal)
  })

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return {
    theme,
    responseLength,
    toggleTheme
  }
})
