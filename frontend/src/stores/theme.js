import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', () => {
  const saved = localStorage.getItem('theme')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const dark = ref(saved ? saved === 'dark' : prefersDark)

  function apply() {
    document.documentElement.setAttribute('data-theme', dark.value ? 'dark' : 'light')
  }

  function toggle() {
    dark.value = !dark.value
  }

  watch(dark, (v) => {
    localStorage.setItem('theme', v ? 'dark' : 'light')
    apply()
  })

  // Apply on init
  apply()

  return { dark, toggle }
})
