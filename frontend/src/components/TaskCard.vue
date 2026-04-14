<template>
  <div
    class="task-card"
    :class="[`prio-${task.priority}`, { overdue: isOverdue, 'is-dragging': dragging }]"
    draggable="true"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @click="$emit('open', task)"
  >
    <div class="task-row">
      <span class="prio-dot" :class="`prio-${task.priority}`" :title="`Priority: ${task.priority}`"></span>
      <span class="task-title">{{ task.title }}</span>
    </div>
    <div v-if="task.description" class="task-desc">{{ truncated }}</div>
    <div class="task-footer">
      <span v-if="task.assignee_username" class="assignee-chip" :title="`Assigned to ${task.assignee_username}`">
        <span class="material-icons-round">person</span>{{ task.assignee_username }}
      </span>
      <span v-else class="assignee-chip muted">
        <span class="material-icons-round">person_off</span>Unassigned
      </span>
      <span v-if="task.deadline" class="deadline-chip" :class="{ overdue: isOverdue }">
        <span class="material-icons-round">schedule</span>{{ fmtDate(task.deadline) }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  task: { type: Object, required: true },
})
const emit = defineEmits(['open', 'drag-start', 'drag-end'])

const dragging = ref(false)

const isOverdue = computed(() => {
  if (!props.task.deadline || props.task.status === 'done') return false
  return new Date(props.task.deadline).getTime() < Date.now()
})

const truncated = computed(() => {
  const d = props.task.description || ''
  return d.length > 120 ? d.slice(0, 120) + '…' : d
})

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function onDragStart(e) {
  dragging.value = true
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(props.task.id))
  emit('drag-start', props.task)
}

function onDragEnd() {
  dragging.value = false
  emit('drag-end', props.task)
}
</script>

<style scoped>
.task-card {
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-left: 3px solid var(--gray-300);
  border-radius: var(--radius-lg);
  padding: 10px 12px;
  cursor: grab;
  user-select: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.task-card:hover { box-shadow: var(--shadow-sm); transform: translateY(-1px); }
.task-card:active { cursor: grabbing; }
.task-card.is-dragging { opacity: 0.45; }

.task-card.prio-high { border-left-color: #dc2626; }
.task-card.prio-medium { border-left-color: #d97706; }
.task-card.prio-low { border-left-color: #059669; }
.task-card.overdue { background: #fef2f2; }

.task-row { display: flex; align-items: center; gap: 8px; }
.prio-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  background: var(--gray-400);
}
.prio-dot.prio-high { background: #dc2626; }
.prio-dot.prio-medium { background: #d97706; }
.prio-dot.prio-low { background: #059669; }

.task-title { font-weight: 500; font-size: .875rem; line-height: 1.3; flex: 1; }
.task-desc {
  font-size: .75rem;
  color: var(--gray-600);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 2px;
}
.assignee-chip, .deadline-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: .6875rem;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: var(--gray-100);
  color: var(--gray-700);
}
.assignee-chip .material-icons-round,
.deadline-chip .material-icons-round { font-size: 13px; }
.assignee-chip.muted { color: var(--gray-500); font-style: italic; }
.deadline-chip.overdue { background: #fee2e2; color: #991b1b; font-weight: 600; }
</style>
