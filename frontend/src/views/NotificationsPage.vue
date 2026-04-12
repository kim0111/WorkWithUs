<template>
  <div class="page container">
    <header class="page-header">
      <h1>Notifications</h1>
      <div class="header-actions">
        <label class="toggle-label">
          <input type="checkbox" v-model="unreadOnly" @change="handleFilterChange" />
          <span>Unread only</span>
        </label>
        <button class="btn btn-secondary btn-sm" @click="markAllRead" :disabled="!store.items.length">
          <span class="material-icons-round">done_all</span>Mark all read
        </button>
      </div>
    </header>
    <div v-if="store.loading" class="notifs-list">
      <div v-for="n in 5" :key="n" class="notif-card" style="pointer-events: none;">
        <div class="notif-icon">
          <SkeletonBlock width="36px" height="36px" border-radius="var(--radius-md)" />
        </div>
        <div class="notif-content" style="display: flex; flex-direction: column; gap: 6px;">
          <SkeletonBlock height="14px" width="60%" />
          <SkeletonBlock height="12px" width="80%" />
          <SkeletonBlock height="10px" width="30%" />
        </div>
      </div>
    </div>
    <div v-else-if="store.items.length" class="notifs-list">
      <div v-for="n in store.items" :key="n.id" class="notif-card" :class="{ unread: !n.is_read }" @click="markRead(n)">
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
import { useNotificationsStore } from '@/stores/notifications'
import { useToastStore } from '@/stores/toast'
import SkeletonBlock from '@/components/SkeletonBlock.vue'

const router = useRouter()
const store = useNotificationsStore()
const toast = useToastStore()
const unreadOnly = ref(false)
const iconMap = { info: 'info', review: 'star', application: 'send', chat: 'chat', warning: 'warning' }

function timeAgo(d) {
  const diff = (Date.now() - new Date(d).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  return Math.floor(diff / 86400) + 'd ago'
}

async function handleFilterChange() {
  await store.fetchList(unreadOnly.value)
}

async function markRead(n) {
  if (!n.is_read) await store.markRead(n.id)
  if (n.link) router.push(n.link)
}

async function markAllRead() {
  await store.markAllRead()
  toast.success('All marked read')
}

onMounted(() => store.fetchList(unreadOnly.value))
</script>
<style scoped>
.page { padding: 2rem 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 10px; }
.header-actions { display: flex; align-items: center; gap: 10px; }
.toggle-label { display: flex; align-items: center; gap: 6px; font-size: .8125rem; color: var(--gray-500); cursor: pointer; }
.toggle-label input { width: 14px; height: 14px; accent-color: var(--accent); }
.notifs-list { display: flex; flex-direction: column; gap: 6px; max-width: 640px; }
.notif-card {
  display: flex; align-items: center; gap: 12px; padding: 12px 16px;
  background: var(--white); border: 1px solid var(--gray-200); border-radius: var(--radius-lg);
  cursor: pointer; transition: all .15s ease;
}
.notif-card.unread { background: var(--accent-light); border-color: rgba(79,70,229,.15); }
.notif-card:hover { border-color: var(--gray-300); }
.notif-icon {
  width: 36px; height: 36px; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  background: var(--gray-100);
}
.notif-icon .material-icons-round { font-size: 18px; color: var(--gray-500); }
.notif-info { background: var(--info-light); } .notif-info .material-icons-round { color: var(--info); }
.notif-review { background: var(--warning-light); } .notif-review .material-icons-round { color: var(--warning); }
.notif-application { background: var(--success-light); } .notif-application .material-icons-round { color: var(--success); }
.notif-chat { background: var(--accent-light); } .notif-chat .material-icons-round { color: var(--accent); }
.notif-content { flex: 1; min-width: 0; }
.notif-title { font-weight: 500; font-size: .875rem; margin-bottom: 1px; }
.notif-message { color: var(--gray-500); font-size: .8125rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.notif-time { font-size: .7rem; color: var(--gray-400); }
.notif-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
.loading-center { display: flex; justify-content: center; padding: 4rem; }
</style>
