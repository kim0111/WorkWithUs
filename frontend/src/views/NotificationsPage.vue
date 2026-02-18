<template>
  <div class="notifications-page container">
    <div class="page-header">
      <h1>Notifications</h1>
      <button class="btn btn-ghost btn-sm" @click="filterUnread = !filterUnread">
        <span class="material-icons-round">{{ filterUnread ? 'notifications_active' : 'notifications' }}</span>
        {{ filterUnread ? 'Unread Only' : 'All' }}
      </button>
    </div>

    <div v-if="loading" class="loading-page"><div class="spinner"></div></div>

    <template v-else>
      <div v-if="notifications.length" class="notif-list">
        <div
          v-for="n in notifications" :key="n.id"
          class="card notif-item"
          :class="{ unread: !n.is_read }"
          @click="markRead(n)"
        >
          <div class="notif-dot" v-if="!n.is_read"></div>
          <div class="notif-content">
            <h4>{{ n.title }}</h4>
            <p v-if="n.message">{{ n.message }}</p>
            <span class="notif-date">{{ formatDate(n.created_at) }}</span>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <span class="material-icons-round">notifications_off</span>
        <h3>No notifications</h3>
        <p>You're all caught up!</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { notificationsAPI } from '@/api'

const notifications = ref([])
const loading = ref(true)
const filterUnread = ref(false)

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''
}

async function fetchNotifications() {
  loading.value = true
  try {
    const { data } = await notificationsAPI.list(filterUnread.value)
    notifications.value = data
  } catch { /* ignore */ }
  loading.value = false
}

async function markRead(n) {
  if (n.is_read) return
  try {
    await notificationsAPI.markRead(n.id)
    n.is_read = true
  } catch { /* ignore */ }
}

watch(filterUnread, fetchNotifications)
onMounted(fetchNotifications)
</script>

<style scoped>
.notifications-page { padding: 2rem; max-width: 720px; }

.page-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;
}

.notif-list { display: flex; flex-direction: column; gap: 8px; }

.notif-item {
  display: flex; align-items: flex-start; gap: 14px; cursor: pointer;
  transition: all 0.2s var(--ease);
}

.notif-item.unread {
  background: var(--bg-card-hover);
  border-color: var(--accent);
}

.notif-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent); margin-top: 8px; flex-shrink: 0;
}

.notif-content h4 {
  font-family: var(--font-body); font-weight: 600; margin-bottom: 4px; font-size: 0.95rem;
}

.notif-content p { color: var(--text-secondary); font-size: 0.88rem; margin-bottom: 6px; }
.notif-date { font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono); }
</style>
