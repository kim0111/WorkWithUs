import { defineStore } from 'pinia'
import { ref } from 'vue'

let _id = 0
export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])
  function add(message, type = 'success') {
    const t = { id: ++_id, message, type }
    toasts.value.push(t)
    setTimeout(() => { toasts.value = toasts.value.filter(x => x.id !== t.id) }, 4000)
  }
  return { toasts, success: m => add(m, 'success'), error: m => add(m, 'error') }
})
