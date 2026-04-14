<template>
  <div class="page container board-page" v-if="project">
    <!-- Header -->
    <div class="board-header">
      <div class="header-left">
        <router-link :to="`/projects/${project.id}`" class="btn btn-ghost btn-sm">
          <span class="material-icons-round">arrow_back</span>Back
        </router-link>
        <div>
          <h1>{{ project.title }}</h1>
          <p class="board-subtitle">Kanban board · {{ totalTasks }} {{ totalTasks === 1 ? 'task' : 'tasks' }}</p>
        </div>
      </div>
      <div class="header-actions">
        <button v-if="canEdit" class="btn btn-primary" @click="openCreate">
          <span class="material-icons-round">add</span>New Task
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="board-filters">
      <div class="filter-group">
        <label class="filter-label">Assignee</label>
        <select class="input select" v-model="filter.assignee" @change="applyFilters">
          <option value="">Everyone</option>
          <option value="__me">Only me</option>
          <option v-for="m in teamMembers" :key="m.user_id" :value="String(m.user_id)">
            {{ m.full_name || m.username }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Priority</label>
        <select class="input select" v-model="filter.priority" @change="applyFilters">
          <option value="">All</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Due before</label>
        <input type="date" class="input" v-model="filter.deadlineBefore" @change="applyFilters" />
      </div>
      <button v-if="hasActiveFilters" class="btn btn-ghost btn-sm" @click="clearFilters">
        <span class="material-icons-round">filter_alt_off</span>Clear
      </button>
    </div>

    <!-- Columns -->
    <div class="board-columns">
      <div
        v-for="col in columns"
        :key="col.id"
        class="board-column"
        :class="{ 'drag-over': dragOverCol === col.id }"
        @dragenter.prevent="dragOverCol = col.id"
        @dragover.prevent
        @dragleave="onDragLeave(col.id, $event)"
        @drop="onDrop(col.id, $event)"
      >
        <div class="column-header">
          <h3>{{ col.label }}</h3>
          <span class="column-count">{{ grouped[col.id].length }}</span>
        </div>
        <div class="column-body">
          <TaskCard
            v-for="task in grouped[col.id]"
            :key="task.id"
            :task="task"
            @open="openDetail"
          />
          <div v-if="!grouped[col.id].length" class="column-empty">No tasks</div>
          <button v-if="canEdit" class="quick-add-btn" @click="openCreate(col.id)">
            <span class="material-icons-round">add</span>Add card
          </button>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <BaseModal v-model="createOpen" title="New Task">
      <form @submit.prevent="createTask" class="create-form">
        <FormField label="Title" required>
          <input class="input" v-model="draft.title" placeholder="e.g. Build login screen" required autofocus />
        </FormField>
        <FormField label="Description">
          <textarea class="input" rows="3" v-model="draft.description" placeholder="Details..."></textarea>
        </FormField>
        <div class="form-row">
          <FormField label="Column">
            <select class="input select" v-model="draft.status">
              <option v-for="c in columns" :key="c.id" :value="c.id">{{ c.label }}</option>
            </select>
          </FormField>
          <FormField label="Priority">
            <select class="input select" v-model="draft.priority">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </FormField>
        </div>
        <div class="form-row">
          <FormField label="Assignee">
            <select class="input select" v-model="draft.assignee_id">
              <option :value="null">Unassigned</option>
              <option v-for="m in assignables" :key="m.user_id" :value="m.user_id">
                {{ m.full_name || m.username }}
              </option>
            </select>
          </FormField>
          <FormField label="Deadline">
            <input type="date" class="input" v-model="draft.deadline" />
          </FormField>
        </div>
      </form>
      <template #footer>
        <button class="btn btn-secondary" @click="createOpen = false">Cancel</button>
        <button class="btn btn-primary" :disabled="!draft.title.trim() || creating" @click="createTask">
          {{ creating ? 'Creating…' : 'Create' }}
        </button>
      </template>
    </BaseModal>

    <!-- Detail drawer -->
    <TaskDetailDrawer
      :task="selectedTask"
      :project-id="project.id"
      :team-members="teamMembers"
      :owner-id="project.owner_id"
      :can-delete="canDelete"
      @close="selectedTask = null"
      @deleted="selectedTask = null"
    />
  </div>
  <div v-else class="page container"><SkeletonBlock :lines="5" /></div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { useProjectsStore } from '@/stores/projects'
import { useTeamsStore } from '@/stores/teams'
import { useTasksStore, TASK_COLUMNS } from '@/stores/tasks'
import TaskCard from '@/components/TaskCard.vue'
import TaskDetailDrawer from '@/components/TaskDetailDrawer.vue'
import BaseModal from '@/components/BaseModal.vue'
import FormField from '@/components/FormField.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()
const projectsStore = useProjectsStore()
const teamsStore = useTeamsStore()
const tasksStore = useTasksStore()

const project = ref(null)
const columns = TASK_COLUMNS
const dragOverCol = ref(null)
const selectedTask = ref(null)

const createOpen = ref(false)
const creating = ref(false)
const draft = reactive({
  title: '', description: '', status: 'todo', priority: 'medium',
  assignee_id: null, deadline: '',
})

const filter = reactive({ assignee: '', priority: '', deadlineBefore: '' })

const projectId = computed(() => Number(route.params.id))
const tasks = computed(() => tasksStore.byProject[projectId.value] || [])
const totalTasks = computed(() => tasks.value.length)
const teamMembers = computed(() => teamsStore.byProject[projectId.value] || [])

const isOwner = computed(() => project.value && auth.user?.id === project.value.owner_id)
const isAdmin = computed(() => auth.isAdmin)
const isTeamMember = computed(() => teamMembers.value.some(m => m.user_id === auth.user?.id))
const canEdit = computed(() => isOwner.value || isAdmin.value || isTeamMember.value)
const canDelete = computed(() => {
  if (isOwner.value || isAdmin.value) return true
  return teamMembers.value.some(m => m.user_id === auth.user?.id && m.is_lead)
})

const assignables = computed(() => {
  const list = [...teamMembers.value]
  if (project.value?.owner_id && !list.some(m => m.user_id === project.value.owner_id)) {
    list.unshift({ user_id: project.value.owner_id, username: 'Owner' })
  }
  return list
})

const grouped = computed(() => {
  const out = { todo: [], in_progress: [], review: [], done: [] }
  for (const t of tasks.value) {
    if (out[t.status]) out[t.status].push(t)
  }
  return out
})

const hasActiveFilters = computed(() =>
  !!(filter.assignee || filter.priority || filter.deadlineBefore)
)

async function load() {
  try {
    await projectsStore.fetchOne(projectId.value)
    project.value = projectsStore.currentProject
    await teamsStore.fetchByProject(projectId.value)
    await applyFilters()
  } catch {
    toast.error('Could not load project')
    router.push('/projects')
  }
}

async function applyFilters() {
  const params = {}
  if (filter.assignee === '__me' && auth.user?.id) params.assignee_id = auth.user.id
  else if (filter.assignee) params.assignee_id = Number(filter.assignee)
  if (filter.priority) params.priority = filter.priority
  if (filter.deadlineBefore) params.deadline_before = new Date(filter.deadlineBefore + 'T23:59:59').toISOString()
  try {
    await tasksStore.fetchByProject(projectId.value, params)
  } catch {
    toast.error('Failed to load tasks')
  }
}

function clearFilters() {
  filter.assignee = ''
  filter.priority = ''
  filter.deadlineBefore = ''
  applyFilters()
}

function openCreate(columnId) {
  draft.title = ''
  draft.description = ''
  draft.status = typeof columnId === 'string' ? columnId : 'todo'
  draft.priority = 'medium'
  draft.assignee_id = null
  draft.deadline = ''
  createOpen.value = true
}

async function createTask() {
  if (!draft.title.trim() || creating.value) return
  creating.value = true
  try {
    const payload = {
      title: draft.title.trim(),
      description: draft.description,
      status: draft.status,
      priority: draft.priority,
      assignee_id: draft.assignee_id,
      deadline: draft.deadline ? new Date(draft.deadline + 'T23:59:59').toISOString() : null,
    }
    await tasksStore.create(projectId.value, payload)
    toast.success('Task created')
    createOpen.value = false
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to create task')
  } finally {
    creating.value = false
  }
}

function onDragLeave(colId, e) {
  // ignore child flicker
  if (e.currentTarget.contains(e.relatedTarget)) return
  if (dragOverCol.value === colId) dragOverCol.value = null
}

async function onDrop(colId, e) {
  dragOverCol.value = null
  const taskId = Number(e.dataTransfer.getData('text/plain'))
  if (!taskId) return
  try {
    await tasksStore.moveTask(projectId.value, taskId, colId)
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Failed to move task')
  }
}

function openDetail(task) {
  selectedTask.value = task
}

// Keep selectedTask in sync when the store updates the task in place
watch(tasks, (list) => {
  if (selectedTask.value) {
    const fresh = list.find(t => t.id === selectedTask.value.id)
    if (fresh) selectedTask.value = fresh
  }
})

onMounted(load)
</script>

<style scoped>
.page { padding: 2rem 24px; }
.board-page { max-width: 1400px; }

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 1rem;
}
.header-left { display: flex; align-items: flex-start; gap: 12px; }
.header-left h1 { margin: 0; font-size: 1.5rem; }
.board-subtitle { margin: 2px 0 0; color: var(--gray-500); font-size: .8125rem; }

.board-filters {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
  padding: 12px 14px;
  background: var(--gray-50, #f9fafb);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
}
.filter-group { display: flex; flex-direction: column; gap: 3px; min-width: 140px; }
.filter-label { font-size: .6875rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--gray-500); font-weight: 600; }

.board-columns {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  align-items: start;
}

.board-column {
  background: var(--gray-100, #f3f4f6);
  border-radius: var(--radius-lg);
  padding: 10px;
  min-height: 200px;
  border: 2px dashed transparent;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.board-column.drag-over {
  border-color: var(--accent);
  background: var(--accent-light, #e0f2fe);
}
.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 6px 10px;
}
.column-header h3 {
  margin: 0;
  font-size: .8125rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--gray-700);
}
.column-count {
  font-size: .75rem;
  color: var(--gray-500);
  background: var(--white);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-weight: 600;
}
.column-body { display: flex; flex-direction: column; gap: 8px; }
.column-empty {
  text-align: center;
  padding: 20px 10px;
  color: var(--gray-400);
  font-size: .8125rem;
  font-style: italic;
}
.quick-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px;
  border: 1px dashed var(--gray-300);
  border-radius: var(--radius-lg);
  background: transparent;
  color: var(--gray-500);
  cursor: pointer;
  font-size: .8125rem;
  transition: all 0.15s ease;
}
.quick-add-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--white);
}

.create-form { display: flex; flex-direction: column; gap: 12px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

@media (max-width: 1000px) {
  .board-columns { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .board-columns { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
}
</style>
