<template>
  <div class="chat-page">
    <!-- Header -->
    <div class="chat-header">
      <router-link to="/chat" class="btn btn-ghost btn-sm"><span class="material-icons-round">arrow_back</span></router-link>
      <div class="chat-header-info">
        <h2>{{ roomInfo?.project_title || 'Chat' }}</h2>
        <span class="chat-status" :class="{ online: wsConnected }">
          {{ wsConnected ? 'Connected' : 'Connecting...' }}
        </span>
      </div>
    </div>

    <!-- Messages -->
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

    <!-- Input -->
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
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function loadHistory() {
  try {
    const { data } = await chatAPI.messages(roomId, 1)
    messages.value = data
  } catch {} finally { loadingHistory.value = false; scrollToBottom() }
}

async function loadRoomInfo() {
  try {
    const { data } = await chatAPI.myRooms()
    roomInfo.value = data.find(r => r.id === roomId) || null
  } catch {}
}

function connectWebSocket() {
  try {
    ws = chatAPI.connectWs(roomId)

    ws.onopen = () => {
      wsConnected.value = true
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        // Avoid duplicates
        if (!messages.value.find(m => m.id === msg.id)) {
          messages.value.push(msg)
          scrollToBottom()
        }
      } catch {}
    }

    ws.onclose = () => {
      wsConnected.value = false
      console.log('WebSocket closed, reconnecting in 3s...')
      setTimeout(connectWebSocket, 3000)
    }

    ws.onerror = () => {
      wsConnected.value = false
    }
  } catch {
    // WebSocket not available, fall back to REST
    wsConnected.value = true // Pretend connected for REST fallback
  }
}

function sendMessage() {
  const content = newMessage.value.trim()
  if (!content) return

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ content }))
    // Optimistic add
    messages.value.push({
      id: 'local-' + Date.now(),
      room_id: roomId,
      sender_id: auth.user.id,
      sender_name: auth.user.full_name || auth.user.username,
      content,
      created_at: new Date().toISOString(),
    })
  } else {
    // REST fallback
    chatAPI.send(roomId, content).then(({ data }) => {
      messages.value.push(data)
    }).catch(() => {})
  }

  newMessage.value = ''
  scrollToBottom()
  nextTick(() => inputRef.value?.focus())
}

// Auto-scroll when new messages arrive
watch(() => messages.value.length, scrollToBottom)

onMounted(() => {
  loadRoomInfo()
  loadHistory()
  connectWebSocket()
  nextTick(() => inputRef.value?.focus())
})

onUnmounted(() => {
  if (ws) {
    ws.onclose = null // Prevent reconnect
    ws.close()
  }
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 72px);
}

/* Header */
.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-secondary);
  flex-shrink: 0;
}
.chat-header-info { flex: 1; }
.chat-header-info h2 { font-size: 1.1rem; margin: 0; }
.chat-status { font-size: .75rem; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }
.chat-status::before { content: ''; width: 8px; height: 8px; border-radius: 50%; background: var(--text-muted); }
.chat-status.online::before { background: var(--success); }
.chat-status.online { color: var(--success); }

/* Messages area */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message {
  max-width: 70%;
  align-self: flex-start;
}
.message.mine {
  align-self: flex-end;
}

.msg-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  padding: 0 4px;
}
.msg-sender { font-size: .78rem; font-weight: 600; color: var(--text-secondary); }
.msg-time { font-size: .7rem; color: var(--text-muted); font-family: var(--font-mono); }

.msg-bubble {
  padding: 10px 16px;
  border-radius: var(--radius-lg);
  font-size: .9rem;
  line-height: 1.5;
  background: var(--bg-card);
  border: 1px solid var(--border);
  word-break: break-word;
}
.message.mine .msg-bubble {
  background: var(--accent);
  color: var(--text-inverse);
  border-color: var(--accent);
}
.message.mine .msg-sender { color: var(--accent); }
.message.mine .msg-header { justify-content: flex-end; }

.empty-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-muted);
}
.empty-chat .material-icons-round { font-size: 48px; opacity: .3; }

/* Input bar */
.chat-input-bar {
  display: flex;
  gap: 10px;
  padding: 14px 24px;
  border-top: 1px solid var(--border);
  background: var(--bg-secondary);
  flex-shrink: 0;
}
.chat-input { flex: 1; }
.send-btn {
  width: 48px;
  height: 48px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
}
.send-btn .material-icons-round { font-size: 20px; }

.loading-center { display: flex; justify-content: center; padding: 2rem; }
</style>
