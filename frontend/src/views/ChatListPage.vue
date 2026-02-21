<template>
  <div class="page container">
    <header class="page-header"><h1><span class="material-icons-round hdr-icon">chat</span>Messages</h1></header>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="rooms.length" class="rooms-list">
      <router-link v-for="r in rooms" :key="r.id" :to="`/chat/${r.id}`" class="room-card card card-interactive">
        <div class="room-icon"><span class="material-icons-round">forum</span></div>
        <div class="room-info">
          <div class="room-title">{{ r.project_title || `Project #${r.project_id}` }}</div>
          <div class="room-participants">
            <span class="material-icons-round">group</span>
            {{ r.participants.length }} participants
          </div>
          <p v-if="r.last_message" class="room-last">{{ r.last_message }}</p>
        </div>
        <div class="room-time" v-if="r.last_message_at">{{ timeAgo(r.last_message_at) }}</div>
      </router-link>
    </div>
    <div v-else class="empty-state">
      <span class="material-icons-round">chat_bubble_outline</span>
      <h3>No conversations yet</h3>
      <p>Start a chat from a project page after applying to a project</p>
      <router-link to="/projects" class="btn btn-primary">Browse Projects</router-link>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { chatAPI } from '@/api'
const rooms = ref([]); const loading = ref(true)
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
.page { padding: 2rem; }
.hdr-icon { font-size: 28px; color: var(--accent); vertical-align: middle; margin-right: 8px; }
.rooms-list { display: flex; flex-direction: column; gap: 10px; max-width: 700px; }
.room-card { display: flex; align-items: center; gap: 16px; padding: 18px 20px; text-decoration: none; color: inherit; }
.room-icon { width: 48px; height: 48px; border-radius: var(--radius-md); background: var(--accent-dim); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.room-icon .material-icons-round { font-size: 24px; color: var(--accent); }
.room-info { flex: 1; min-width: 0; }
.room-title { font-weight: 600; font-size: 1rem; margin-bottom: 3px; }
.room-participants { display: flex; align-items: center; gap: 4px; font-size: .78rem; color: var(--text-muted); margin-bottom: 4px; }
.room-participants .material-icons-round { font-size: 14px; }
.room-last { font-size: .85rem; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.room-time { font-size: .78rem; color: var(--text-muted); font-family: var(--font-mono); white-space: nowrap; }
.loading-center { display: flex; justify-content: center; padding: 4rem; }
</style>
