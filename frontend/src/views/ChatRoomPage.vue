<template>
  <div class="chat-page">
    <div class="chat-header">
      <router-link to="/chat" class="btn btn-ghost btn-sm"><span class="material-icons-round">arrow_back</span></router-link>
      <div class="chat-header-info">
        <h2>{{ roomInfo?.project_title || 'Chat' }}</h2>
        <span class="chat-status" :class="{ online: wsConnected }">
          {{ wsConnected ? 'Connected' : 'Connecting...' }}
        </span>
      </div>
    </div>

    <div class="messages-area" ref="messagesContainer">
      <div v-if="loadingHistory" class="loading-center"><div class="spinner"></div></div>
      <div v-for="(msg, i) in messages" :key="msg.id || i" class="message" :class="{ mine: msg.sender_id === auth.user?.id }">
        <div class="msg-header">
          <span class="msg-sender">{{ msg.sender_name }}</span>
          <span class="msg-time">{{ fmtTime(msg.created_at) }}</span>
        </div>
        <div class="msg-bubble">{{ msg.content }}</div>
      </div>
      <div v-if="!loadingHistory && messages.length === 0" class="empty-chat">
        <span class="material-icons-round">chat_bubble_outline</span>
        <p>No messages yet. Say hello!</p>
      </div>
    </div>

    <form class="chat-input-bar" @submit.prevent="sendMessage">
      <input
        class="input chat-input"
        v-model="newMessage"
        placeholder="Type a message..."
        :disabled="!wsConnected"
        @keydown.enter.exact.prevent="sendMessage"
        ref="inputRef"
      />
      <button type="submit" class="btn btn-primary send-btn" :disabled="!newMessage.trim() || !wsConnected">
        <span class="material-icons-round">send</span>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { chatAPI } from '@/api'

const route = useRoute()
const auth = useAuthStore()
const roomId = route.params.roomId

const messages = ref([])
const newMessage = ref('')
const roomInfo = ref(null)
const wsConnected = ref(false)
const loadingHistory = ref(true)
const messagesContainer = ref(null)
const inputRef = ref(null)

let ws = null

function fmtTime(d) {
  if (!d) return ''
  const dt = new Date(d)
  const now = new Date()
  const isToday = dt.toDateString() === now.toDateString()
  if (isToday) return dt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + dt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}

async function loadHistory() {
  try { const { data } = await chatAPI.messages(roomId, 1); messages.value = data }
  catch {} finally { loadingHistory.value = false; scrollToBottom() }
}

async function loadRoomInfo() {
  try { const { data } = await chatAPI.myRooms(); roomInfo.value = data.find(r => r.id === roomId) || null } catch {}
}

function connectWebSocket() {
  try {
    ws = chatAPI.connectWs(roomId)
    ws.onopen = () => { wsConnected.value = true }
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        // Replace optimistic local message if it matches
        const localIdx = messages.value.findIndex(
          m => typeof m.id === 'string' && m.id.startsWith('local-') && m.sender_id === msg.sender_id && m.content === msg.content
        )
        if (localIdx !== -1) { messages.value[localIdx] = msg }
        else if (!messages.value.find(m => m.id === msg.id)) { messages.value.push(msg); scrollToBottom() }
      } catch {}
    }
    ws.onclose = () => { wsConnected.value = false; setTimeout(connectWebSocket, 3000) }
    ws.onerror = () => { wsConnected.value = false }
  } catch { wsConnected.value = true }
}

function sendMessage() {
  const content = newMessage.value.trim()
  if (!content) return
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ content }))
    messages.value.push({
      id: 'local-' + Date.now(), room_id: roomId, sender_id: auth.user.id,
      sender_name: auth.user.full_name || auth.user.username,
      content, created_at: new Date().toISOString(),
    })
  } else {
    chatAPI.send(roomId, content).then(({ data }) => { messages.value.push(data) }).catch(() => {})
  }
  newMessage.value = ''
  scrollToBottom()
  nextTick(() => inputRef.value?.focus())
}

watch(() => messages.value.length, scrollToBottom)

onMounted(() => { loadRoomInfo(); loadHistory(); connectWebSocket(); nextTick(() => inputRef.value?.focus()) })
onUnmounted(() => { if (ws) { ws.onclose = null; ws.close() } })
</script>

<style scoped>
.chat-page { display: flex; flex-direction: column; height: calc(100vh - 56px); }

.chat-header {
  display: flex; align-items: center; gap: 10px; padding: 10px 20px;
  border-bottom: 1px solid var(--gray-200); background: var(--white); flex-shrink: 0;
}
.chat-header-info { flex: 1; }
.chat-header-info h2 { font-size: .9375rem; margin: 0; }
.chat-status { font-size: .7rem; color: var(--gray-400); display: flex; align-items: center; gap: 4px; }
.chat-status::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: var(--gray-300); }
.chat-status.online::before { background: var(--success); }
.chat-status.online { color: var(--success); }

.messages-area { flex: 1; overflow-y: auto; padding: 16px 20px; display: flex; flex-direction: column; gap: 8px; background: var(--gray-50); }

.message { max-width: 70%; align-self: flex-start; }
.message.mine { align-self: flex-end; }
.msg-header { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; padding: 0 2px; }
.msg-sender { font-size: .75rem; font-weight: 500; color: var(--gray-500); }
.msg-time { font-size: .675rem; color: var(--gray-400); }
.msg-bubble {
  padding: 8px 14px; border-radius: var(--radius-lg); font-size: .8125rem; line-height: 1.5;
  background: var(--white); border: 1px solid var(--gray-200); word-break: break-word;
}
.message.mine .msg-bubble { background: var(--accent); color: white; border-color: var(--accent); }
.message.mine .msg-sender { color: var(--accent-text); }
.message.mine .msg-header { justify-content: flex-end; }

.empty-chat { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; color: var(--gray-400); }
.empty-chat .material-icons-round { font-size: 40px; color: var(--gray-300); }
.empty-chat p { font-size: .8125rem; }

.chat-input-bar { display: flex; gap: 8px; padding: 10px 20px; border-top: 1px solid var(--gray-200); background: var(--white); flex-shrink: 0; }
.chat-input { flex: 1; }
.send-btn {
  width: 40px; height: 40px; padding: 0; display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md);
}
.send-btn .material-icons-round { font-size: 18px; }
.loading-center { display: flex; justify-content: center; padding: 2rem; }
</style>
