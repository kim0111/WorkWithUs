<template>
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div v-if="application" class="drawer-backdrop" @click.self="close">
        <aside class="drawer" role="dialog" aria-modal="true" aria-labelledby="app-drawer-title">
          <header class="drawer-head">
            <h3 id="app-drawer-title">Application details</h3>
            <button class="drawer-close" @click="close" aria-label="Close">
              <span class="material-icons-round">close</span>
            </button>
          </header>

          <div class="drawer-body">
            <div class="app-summary">
              <div class="summary-top">
                <div class="summary-title">Project #{{ application.project_id }}</div>
                <StatusBadge :status="application.status" size="md" />
              </div>
              <p v-if="application.cover_letter" class="cover-letter">
                <strong>Cover letter:</strong> {{ application.cover_letter }}
              </p>
            </div>

            <h4 class="section-heading">Timeline</h4>
            <ApplicationTimeline :history="application.status_history || []" />
            <p v-if="!application.status_history?.length" class="no-history">
              No history recorded yet — future changes will appear here.
            </p>

            <div v-if="noteFor" class="note-input">
              <textarea
                class="input"
                v-model="noteText"
                rows="3"
                :placeholder="noteFor === 'submitted' ? 'Submission note...' : 'Revision note...'"
              ></textarea>
              <div class="note-actions">
                <button class="btn btn-ghost btn-sm" @click="cancelNote">Cancel</button>
                <button class="btn btn-primary btn-sm" @click="confirmNote" :disabled="busy">
                  {{ busy ? 'Saving...' : 'Confirm' }}
                </button>
              </div>
            </div>

            <p v-if="errorMsg" class="drawer-error">{{ errorMsg }}</p>
          </div>

          <footer v-if="actionButtons.length && !noteFor" class="drawer-foot">
            <button
              v-for="btn in actionButtons"
              :key="btn.status"
              :class="btn.class"
              :disabled="busy"
              @click="onAction(btn)"
            >
              <span v-if="btn.icon" class="material-icons-round">{{ btn.icon }}</span>
              {{ btn.label }}
            </button>
          </footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useApplicationsStore } from '@/stores/applications'
import ApplicationTimeline from '@/components/ApplicationTimeline.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const props = defineProps({
  application: { type: Object, default: null },
  viewAs: { type: String, required: true, validator: v => ['student', 'company'].includes(v) },
})
const emit = defineEmits(['close', 'action-complete'])

const store = useApplicationsStore()
const busy = ref(false)
const errorMsg = ref('')
const noteFor = ref(null)   // 'submitted' | 'revision_requested' | null
const noteText = ref('')

function close() {
  if (busy.value) return
  errorMsg.value = ''
  noteFor.value = null
  noteText.value = ''
  emit('close')
}

const actionButtons = computed(() => {
  if (!props.application) return []
  const s = props.application.status
  if (props.viewAs === 'student') {
    if (s === 'accepted') return [{ status: 'in_progress', label: 'Start Working', icon: 'play_arrow', class: 'btn btn-primary btn-sm' }]
    if (s === 'in_progress' || s === 'revision_requested') return [{ status: 'submitted', label: 'Submit Work', icon: 'send', class: 'btn btn-primary btn-sm', requiresNote: true }]
    return []
  }
  if (props.viewAs === 'company') {
    if (s === 'pending') return [
      { status: 'accepted', label: 'Accept', icon: 'check', class: 'btn btn-primary btn-sm' },
      { status: 'rejected', label: 'Reject', icon: 'close', class: 'btn btn-danger btn-sm' },
    ]
    if (s === 'submitted') return [
      { status: 'approved', label: 'Approve', icon: 'check_circle', class: 'btn btn-primary btn-sm' },
      { status: 'revision_requested', label: 'Request Revision', icon: 'edit_note', class: 'btn btn-outline btn-sm', requiresNote: true },
    ]
    if (s === 'approved') return [{ status: 'completed', label: 'Mark Completed', icon: 'task_alt', class: 'btn btn-primary btn-sm' }]
  }
  return []
})

function onAction(btn) {
  errorMsg.value = ''
  if (btn.requiresNote) {
    noteFor.value = btn.status
    noteText.value = ''
    return
  }
  runUpdate(btn.status, null)
}

function cancelNote() {
  noteFor.value = null
  noteText.value = ''
}

async function confirmNote() {
  if (!noteText.value.trim()) {
    errorMsg.value = 'Please enter a note before confirming.'
    return
  }
  await runUpdate(noteFor.value, noteText.value.trim())
}

async function runUpdate(status, note) {
  busy.value = true
  errorMsg.value = ''
  try {
    await store.updateStatus(props.application.id, { status, note })
    noteFor.value = null
    noteText.value = ''
    emit('action-complete')
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Could not update status — please try again.'
  } finally {
    busy.value = false
  }
}

function onEsc(e) { if (e.key === 'Escape') close() }
onMounted(() => window.addEventListener('keydown', onEsc))
onUnmounted(() => window.removeEventListener('keydown', onEsc))

watch(() => props.application, (val) => {
  if (!val) {
    errorMsg.value = ''
    noteFor.value = null
    noteText.value = ''
  }
})
</script>

<style scoped>
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
}
.drawer {
  width: 420px;
  max-width: 100vw;
  height: 100%;
  background: var(--white);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}
.drawer-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--gray-200);
}
.drawer-head h3 { font-size: 1rem; margin: 0; }
.drawer-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--gray-500);
  padding: 4px;
  display: flex;
  align-items: center;
}
.drawer-close:hover { color: var(--gray-900); }
.drawer-body {
  flex: 1;
  padding: 16px 20px;
  overflow-y: auto;
}
.app-summary {
  padding: 12px;
  background: var(--gray-50);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}
.summary-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.summary-title { font-weight: 600; font-size: .9375rem; }
.cover-letter { font-size: .8125rem; color: var(--gray-700); line-height: 1.5; margin: 0; }
.section-heading { font-size: .875rem; font-weight: 600; margin: 0 0 10px; color: var(--gray-700); }
.no-history { font-size: .8125rem; color: var(--gray-500); padding: 8px 0; }
.note-input {
  margin-top: 16px;
  padding: 12px;
  background: var(--gray-50);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.note-actions { display: flex; justify-content: flex-end; gap: 8px; }
.drawer-error {
  margin-top: 10px;
  padding: 8px 10px;
  font-size: .8125rem;
  color: var(--danger);
  background: var(--danger-light);
  border-radius: var(--radius-md);
}
.drawer-foot {
  padding: 12px 20px;
  border-top: 1px solid var(--gray-200);
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  background: var(--white);
}

.drawer-fade-enter-active .drawer { transition: transform .2s ease; }
.drawer-fade-leave-active .drawer { transition: transform .2s ease; }
.drawer-fade-enter-from .drawer { transform: translateX(100%); }
.drawer-fade-leave-to .drawer { transform: translateX(100%); }
.drawer-fade-enter-active { transition: opacity .2s ease; }
.drawer-fade-leave-active { transition: opacity .2s ease; }
.drawer-fade-enter-from, .drawer-fade-leave-to { opacity: 0; }
</style>
