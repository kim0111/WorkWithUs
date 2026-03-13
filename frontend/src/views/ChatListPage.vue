<template>
  <div class="page container">
    <header class="page-header"><h1>Messages</h1></header>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="rooms.length" class="rooms-list">
      <router-link v-for="r in rooms" :key="r.id" :to="`/chat/${r.id}`" class="room-card card card-interactive">
        <div class="room-icon"><span class="material-icons-round">chat_bubble_outline</span></div>
        <div class="room-info">
          <div class="room-title">{{ r.project_title || `Project #${r.project_id}` }}</div>
          <div class="room-participants">{{ r.participants.length }} participants</div>
          <p v-if="r.last_message" class="room-last">{{ r.last_message }}</p>
        </div>
        <div class="room-time" v-if="r.last_message_at">{{ timeAgo(r.last_message_at) }}</div>
      </router-link>
    </div>
    <div v-else class="empty-state">
      <span class="material-icons-round">chat_bubble_outline</span>
      <h3>No conversations yet</h3>
      <p>Start a chat from a project page after applying</p>
      <router-link to="/projects" class="btn btn-primary">Browse Projects</router-link>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { chatAPI } from '@/api'

const rooms = ref([])
const loading = ref(true)

function timeAgo(d) {
  const diff = (Date.now() - new Date(d).getTime()) / 1000
  if (diff < 60) return 'now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  return Math.floor(diff / 86400) + 'd ago'
}

onMounted(async () => { try { rooms.value = (await chatAPI.myRooms()).data } catch {} finally { loading.value = false } })
</script>
<style scoped>
.page { padding: 2rem 24px; }
.page-header { margin-bottom: 1.5rem; }
.rooms-list { display: flex; flex-direction: column; gap: 8px; max-width: 640px; }
.room-card { display: flex; align-items: center; gap: 12px; padding: 14px 16px; text-decoration: none; color: inherit; }
.room-icon {
  width: 40px; height: 40px; border-radius: var(--radius-md); background: var(--accent-light);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.room-icon .material-icons-round { font-size: 20px; color: var(--accent); }
.room-info { flex: 1; min-width: 0; }
.room-title { font-weight: 500; font-size: .875rem; margin-bottom: 1px; }
.room-participants { font-size: .75rem; color: var(--gray-400); margin-bottom: 2px; }
.room-last { font-size: .8125rem; color: var(--gray-500); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.room-time { font-size: .75rem; color: var(--gray-400); white-space: nowrap; }
.loading-center { display: flex; justify-content: center; padding: 4rem; }
</style>
