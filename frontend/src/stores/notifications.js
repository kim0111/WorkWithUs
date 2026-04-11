import { defineStore } from 'pinia'
import { ref } from 'vue'
import { notificationsAPI } from '@/api'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref([])
  const unreadCount = ref(0)
  const loading = ref(false)

  async function fetchUnreadCount() {
    try {
      unreadCount.value = (await notificationsAPI.unreadCount()).data.count
    } catch {}
  }

  async function fetchList(unreadOnly = false) {
    loading.value = true
    try {
      items.value = (await notificationsAPI.list(unreadOnly)).data
    } catch {} finally {
      loading.value = false
    }
  }

  async function markRead(id) {
    try {
      await notificationsAPI.markRead(id)
      const item = items.value.find(n => n.id === id)
      if (item && !item.is_read) {
        item.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch {}
  }

  async function markAllRead() {
    try {
      await notificationsAPI.markAllRead()
      items.value.forEach(n => { n.is_read = true })
      unreadCount.value = 0
    } catch {}
  }

  let pollInterval = null

  function startPolling() {
    if (pollInterval) return
    fetchUnreadCount()
    pollInterval = setInterval(fetchUnreadCount, 30000)
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  return {
    items, unreadCount, loading,
    fetchUnreadCount, fetchList, markRead, markAllRead,
    startPolling, stopPolling,
  }
})
