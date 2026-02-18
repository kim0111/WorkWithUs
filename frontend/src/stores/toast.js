import { defineStore } from 'pinia'
import { ref } from 'vue'

let id = 0

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function add(message, type = 'success') {
    const toast = { id: ++id, message, type }
    toasts.value.push(toast)
    setTimeout(() => remove(toast.id), 4000)
  }

  function remove(toastId) {
    toasts.value = toasts.value.filter(t => t.id !== toastId)
  }

  function success(msg) { add(msg, 'success') }
  function error(msg) { add(msg, 'error') }

  return { toasts, add, remove, success, error }
})
