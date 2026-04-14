<template>
  <BaseModal :model-value="!!task" @update:model-value="$emit('close')" :title="task?.title || 'Task'" max-width="640px">
    <div v-if="task" class="task-detail">
      <!-- Top meta row -->
      <div class="meta-grid">
        <FormField label="Status">
          <select class="input select" :value="form.status" @change="onFieldChange('status', $event.target.value)">
            <option v-for="c in columns" :key="c.id" :value="c.id">{{ c.label }}</option>
          </select>
        </FormField>
        <FormField label="Priority">
          <select class="input select" :value="form.priority" @change="onFieldChange('priority', $event.target.value)">
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </FormField>
        <FormField label="Assignee">
          <select class="input select" :value="form.assignee_id ?? ''" @change="onAssigneeChange">
            <option value="">Unassigned</option>
            <option v-for="m in assignables" :key="m.user_id" :value="m.user_id">
              {{ m.full_name || m.username }}
            </option>
          </select>
        </FormField>
        <FormField label="Deadline">
          <input type="date" class="input" :value="deadlineInput" @change="onDeadlineChange" />
        </FormField>
      </div>

      <!-- Title/description edit -->
      <FormField label="Title">
        <input class="input" v-model="form.title" @blur="syncIfChanged('title')" />
      </FormField>
      <FormField label="Description">
        <textarea class="input" rows="4" v-model="form.description" @blur="syncIfChanged('description')"
          placeholder="Add more detail..."></textarea>
      </FormField>

      <!-- Tabs: Comments + Activity -->
      <BaseTabs
        v-model="tab"
        :tabs="[
          { key: 'comments', label: 'Comments', count: comments.length },
          { key: 'activity', label: 'Activity', count: activity.length },
        ]"
      />

      <div v-if="tab === 'comments'" class="comments-panel">
        <div v-if="comments.length" class="comments-list">
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <div class="comment-head">
              <span class="av-sm">{{ (c.author_username || '?').charAt(0).toUpperCase() }}</span>
              <span class="comment-author">{{ c.author_username }}</span>
              <span class="comment-time">{{ fmtDateTime(c.created_at) }}</span>
            </div>
            <p class="comment-body">{{ c.content }}</p>
          </div>
        </div>
        <EmptyState v-else icon="forum" title="No comments yet" subtitle="Start the discussion" />

        <form class="comment-form" @submit.prevent="submitComment">
          <textarea class="input" rows="2" v-model="newComment" placeholder="Write a comment..."></textarea>
          <button type="submit" class="btn btn-primary btn-sm" :disabled="!newComment.trim() || posting">
            {{ posting ? 'Posting…' : 'Post' }}
          </button>
        </form>
      </div>

      <div v-else class="activity-panel">
        <div v-if="activity.length" class="activity-list">
          <div v-for="a in activity" :key="a.id" class="activity-item">
            <span class="activity-time">{{ fmtDateTime(a.created_at) }}</span>
            <span class="activity-text">
              <strong>{{ a.actor_username }}</strong>
              {{ describeAction(a) }}
            </span>
          </div>
        </div>
        <EmptyState v-else icon="history" title="No activity yet" />
      </div>
    </div>

    <template #footer>
      <button v-if="canDelete" class="btn btn-ghost btn-danger-text" @click="confirmDelete = true">
        <span class="material-icons-round">delete</span>Delete
      </button>
      <div style="flex: 1"></div>
      <button class="btn btn-secondary" @click="$emit('close')">Close</button>
    </template>
  </BaseModal>

  <ConfirmDialog
    v-model="confirmDelete"
    title="Delete task"
    message="This cannot be undone."
    @confirm="onDelete"
  />
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import BaseTabs from '@/components/BaseTabs.vue'
import FormField from '@/components/FormField.vue'
import EmptyState from '@/components/EmptyState.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useTasksStore, TASK_COLUMNS } from '@/stores/tasks'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  task: { type: Object, default: null },
  projectId: { type: Number, required: true },
  teamMembers: { type: Array, default: () => [] },
  ownerId: { type: Number, default: null },
  canDelete: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'deleted'])

const tasksStore = useTasksStore()
const toast = useToastStore()
const columns = TASK_COLUMNS

const form = reactive({
  title: '',
  description: '',
  status: 'todo',
  priority: 'medium',
  assignee_id: null,
  deadline: null,
})
const tab = ref('comments')
const comments = ref([])
const activity = ref([])
const newComment = ref('')
const posting = ref(false)
const confirmDelete = ref(false)

const assignables = computed(() => {
  const list = [...props.teamMembers]
  if (props.ownerId && !list.some(m => m.user_id === props.ownerId)) {
    list.unshift({ user_id: props.ownerId, username: 'Owner' })
  }
  return list
})

const deadlineInput = computed(() => {
  if (!form.deadline) return ''
  return new Date(form.deadline).toISOString().slice(0, 10)
})

watch(() => props.task, async (t) => {
  if (!t) return
  form.title = t.title
  form.description = t.description || ''
  form.status = t.status
  form.priority = t.priority
  form.assignee_id = t.assignee_id
  form.deadline = t.deadline
  tab.value = 'comments'
  await refreshComments()
  await refreshActivity()
}, { immediate: true })

async function refreshComments() {
  if (!props.task) return
  try { comments.value = await tasksStore.listComments(props.task.id) } catch {}
}

async function refreshActivity() {
  if (!props.task) return
  try { activity.value = await tasksStore.listActivity(props.task.id) } catch {}
}

async function onFieldChange(field, value) {
  form[field] = value
  await patch({ [field]: value })
  await refreshActivity()
}

async function onAssigneeChange(e) {
  const raw = e.target.value
  const id = raw === '' ? null : Number(raw)
  form.assignee_id = id
  await patch({ assignee_id: id })
  await refreshActivity()
}

async function onDeadlineChange(e) {
  const val = e.target.value
  const iso = val ? new Date(val + 'T23:59:59').toISOString() : null
  form.deadline = iso
  await patch({ deadline: iso })
  await refreshActivity()
}

async function syncIfChanged(field) {
  if (!props.task) return
  const current = props.task[field] || (field === 'description' ? '' : '')
  if (form[field] === current) return
  await patch({ [field]: form[field] })
  await refreshActivity()
}

async function patch(payload) {
  try {
    await tasksStore.update(props.projectId, props.task.id, payload)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to update task')
  }
}

async function submitComment() {
  if (!newComment.value.trim()) return
  posting.value = true
  try {
    const c = await tasksStore.addComment(props.task.id, newComment.value.trim())
    comments.value.push(c)
    newComment.value = ''
    await refreshActivity()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to post comment')
  } finally {
    posting.value = false
  }
}

async function onDelete() {
  confirmDelete.value = false
  try {
    await tasksStore.remove(props.projectId, props.task.id)
    toast.success('Task deleted')
    emit('deleted', props.task.id)
    emit('close')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to delete task')
  }
}

function fmtDateTime(d) {
  return new Date(d).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function describeAction(a) {
  switch (a.action) {
    case 'created': return `created this task`
    case 'status': return `moved ${a.from_value || '?'} → ${a.to_value || '?'}`
    case 'priority': return `changed priority ${a.from_value || '?'} → ${a.to_value || '?'}`
    case 'assignee': return a.to_value ? `assigned to user #${a.to_value}` : `cleared the assignee`
    case 'deadline': return `updated the deadline`
    case 'title': return `renamed title`
    case 'description': return `updated description`
    case 'commented': return `commented`
    default: return a.action
  }
}
</script>

<style scoped>
.task-detail { display: flex; flex-direction: column; gap: 14px; }
.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.comments-panel, .activity-panel { display: flex; flex-direction: column; gap: 10px; }

.comments-list { display: flex; flex-direction: column; gap: 10px; max-height: 260px; overflow-y: auto; }
.comment-item {
  background: var(--gray-50, #f9fafb);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: 10px 12px;
}
.comment-head { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.comment-author { font-weight: 600; font-size: .8125rem; }
.comment-time { font-size: .75rem; color: var(--gray-500); margin-left: auto; }
.comment-body { margin: 0; font-size: .875rem; line-height: 1.4; white-space: pre-wrap; }

.av-sm {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--accent); color: white;
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; font-size: .75rem;
}

.comment-form { display: flex; gap: 8px; align-items: flex-end; }
.comment-form textarea { flex: 1; resize: vertical; }

.activity-list { display: flex; flex-direction: column; gap: 6px; max-height: 260px; overflow-y: auto; }
.activity-item {
  display: flex; flex-direction: column;
  padding: 6px 10px;
  border-left: 2px solid var(--gray-200);
  font-size: .8125rem;
}
.activity-time { font-size: .6875rem; color: var(--gray-500); }
.btn-danger-text { color: var(--danger); }

@media (max-width: 520px) {
  .meta-grid { grid-template-columns: 1fr; }
}
</style>
