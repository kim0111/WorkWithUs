<template>
  <div class="page container">
    <header class="page-header">
      <h1>Notifications</h1>
      <div class="header-actions">
        <label class="toggle-label">
          <input type="checkbox" v-model="unreadOnly" @change="fetchNotifs" />
          <span>Unread only</span>
        </label>
        <button class="btn btn-secondary btn-sm" @click="markAllRead" :disabled="!notifs.length">
          <span class="material-icons-round">done_all</span>Mark all read
        </button>
      </div>
    </header>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="notifs.length" class="notifs-list">
      <div v-for="n in notifs" :key="n.id" class="notif-card card" :class="{ unread: !n.is_read }" @click="markRead(n)">
        <div class="notif-icon" :class="`notif-${n.notification_type}`">
          <span class="material-icons-round">{{ iconMap[n.notification_type] || 'notifications' }}</span>
        </div>
        <div class="notif-content">
          <div class="notif-title">{{ n.title }}</div>
          <p v-if="n.message" class="notif-message">{{ n.message }}</p>
          <span class="notif-time">{{ timeAgo(n.created_at) }}</span>
        </div>
        <div v-if="!n.is_read" class="notif-dot"></div>
      </div>
    </div>
    <div v-else class="empty-state">
      <span class="material-icons-round">notifications_none</span>
      <h3>{{ unreadOnly ? 'No unread notifications' : 'No notifications yet' }}</h3>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationsAPI } from '@/api'
import { useToastStore } from '@/stores/toast'
const router = useRouter(); const toast = useToastStore()
const notifs = ref([]); const loading = ref(true); const unreadOnly = ref(false)
const iconMap = { info: 'info', review: 'star', application: 'send', chat: 'chat', warning: 'warning' }

function timeAgo(d) {
  const diff = (Date.now() - new Date(d).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  return Math.floor(diff / 86400) + 'd ago'
}

async function fetchNotifs() {
  loading.value = true
  try { notifs.value = (await notificationsAPI.list(unreadOnly.value)).data }
  catch {} finally { loading.value = false }
}

async function markRead(n) {
  if (!n.is_read) {
    try { await notificationsAPI.markRead(n.id); n.is_read = true } catch {}
  }
  if (n.link) router.push(n.link)
}

async function markAllRead() {
  try { await notificationsAPI.markAllRead(); notifs.value.forEach(n => n.is_read = true); toast.success('All marked read') }
  catch {}
}

onMounted(fetchNotifs)
</script>
<style scoped>
.page { padding: 2rem; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; flex-wrap: wrap; gap: 12px; }
.header-actions { display: flex; align-items: center; gap: 14px; }
.toggle-label { display: flex; align-items: center; gap: 8px; font-size: .85rem; color: var(--text-secondary); cursor: pointer; }
.toggle-label input { width: 16px; height: 16px; accent-color: var(--accent); }
.notifs-list { display: flex; flex-direction: column; gap: 8px; max-width: 700px; }
.notif-card { display: flex; align-items: center; gap: 14px; padding: 16px 20px; cursor: pointer; transition: all .2s var(--ease); }
.notif-card.unread { background: var(--bg-secondary); border-color: var(--border-strong); }
.notif-card:hover { border-color: var(--accent); }
.notif-icon { width: 40px; height: 40px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: var(--bg-card); }
.notif-icon .material-icons-round { font-size: 20px; }
.notif-info { background: rgba(96,165,250,.12); } .notif-info .material-icons-round { color: #60a5fa; }
.notif-review { background: var(--accent-dim); } .notif-review .material-icons-round { color: var(--accent); }
.notif-application { background: var(--teal-dim); } .notif-application .material-icons-round { color: var(--teal); }
.notif-chat { background: rgba(192,132,252,.12); } .notif-chat .material-icons-round { color: #c084fc; }
.notif-content { flex: 1; min-width: 0; }
.notif-title { font-weight: 600; font-size: .95rem; margin-bottom: 2px; }
.notif-message { color: var(--text-secondary); font-size: .85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.notif-time { font-size: .75rem; color: var(--text-muted); font-family: var(--font-mono); }
.notif-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
.loading-center { display: flex; justify-content: center; padding: 4rem; }
</style>
