<template>
  <div class="page container">
    <header class="page-header"><h1>My Applications</h1></header>
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="apps.length" class="apps-list">
      <div v-for="a in apps" :key="a.id" class="app-card card">
        <div class="app-header">
          <router-link :to="`/projects/${a.project_id}`" class="app-project-link">
            <span class="material-icons-round">folder</span>Project #{{ a.project_id }}
          </router-link>
          <span class="badge" :class="statusBadge(a.status)">{{ a.status }}</span>
        </div>
        <p v-if="a.cover_letter" class="app-letter">{{ a.cover_letter }}</p>
        <p v-if="a.submission_note" class="status-note"><span class="material-icons-round">send</span>{{ a.submission_note }}</p>
        <p v-if="a.revision_note" class="status-note revision"><span class="material-icons-round">edit_note</span>{{ a.revision_note }}</p>

        <div class="workflow-bar">
          <div v-for="s in workflowSteps" :key="s" class="wf-step" :class="{ done: stepIndex(a.status) >= workflowSteps.indexOf(s), current: a.status === s }">
            <div class="wf-dot"></div>
            <span class="wf-label">{{ s }}</span>
          </div>
        </div>

        <div class="app-footer">
          <span class="text-muted">Applied {{ fmtDate(a.created_at) }}</span>
          <span class="text-muted">Updated {{ fmtDate(a.updated_at) }}</span>
          <router-link :to="`/projects/${a.project_id}`" class="btn btn-ghost btn-sm">
            <span class="material-icons-round">open_in_new</span>View Project
          </router-link>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">
      <span class="material-icons-round">send</span>
      <h3>No applications yet</h3>
      <p>Browse projects and apply to get started</p>
      <router-link to="/projects" class="btn btn-primary">Browse Projects</router-link>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { applicationsAPI } from '@/api'

const apps = ref([])
const loading = ref(true)
const workflowSteps = ['pending', 'accepted', 'in_progress', 'submitted', 'approved', 'completed']

function stepIndex(s) { const i = workflowSteps.indexOf(s); return i >= 0 ? i : (s === 'rejected' ? -1 : s === 'revision_requested' ? 3 : 0) }
function statusBadge(s) {
  return { pending: 'badge-info', accepted: 'badge-success', rejected: 'badge-danger', in_progress: 'badge-warning',
    submitted: 'badge-accent', revision_requested: 'badge-warning', approved: 'badge-success', completed: 'badge-teal' }[s] || 'badge-info'
}
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '' }

onMounted(async () => { try { apps.value = (await applicationsAPI.my()).data } catch {} finally { loading.value = false } })
</script>
<style scoped>
.page { padding: 2rem 24px; }
.page-header { margin-bottom: 1.5rem; }
.apps-list { display: flex; flex-direction: column; gap: 12px; }
.app-card { padding: 20px; }
.app-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.app-project-link { display: flex; align-items: center; gap: 6px; text-decoration: none; color: var(--gray-900); font-weight: 500; font-size: .9375rem; }
.app-project-link .material-icons-round { color: var(--accent); font-size: 18px; }
.app-letter { color: var(--gray-600); font-size: .8125rem; margin-bottom: 10px; line-height: 1.5; }
.status-note { display: flex; align-items: center; gap: 6px; font-size: .8125rem; color: var(--gray-600); padding: 6px 10px; background: var(--gray-50); border-radius: var(--radius-md); margin-bottom: 6px; }
.status-note.revision { color: var(--warning); background: var(--warning-light); }
.status-note .material-icons-round { font-size: 16px; }

.workflow-bar { display: flex; gap: 0; margin: 14px 0; overflow-x: auto; }
.wf-step { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; min-width: 60px; position: relative; }
.wf-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--gray-100); border: 2px solid var(--gray-300); transition: all .15s; z-index: 1; }
.wf-step.done .wf-dot { background: var(--accent); border-color: var(--accent); }
.wf-step.current .wf-dot { background: var(--accent); border-color: var(--accent); box-shadow: 0 0 0 3px rgba(79,70,229,.15); }
.wf-label { font-size: .625rem; color: var(--gray-400); text-transform: uppercase; letter-spacing: .02em; text-align: center; }
.wf-step.done .wf-label, .wf-step.current .wf-label { color: var(--gray-700); font-weight: 600; }
.wf-step:not(:last-child)::after { content: ''; position: absolute; top: 4px; left: calc(50% + 7px); right: calc(-50% + 7px); height: 2px; background: var(--gray-200); }
.wf-step.done:not(:last-child)::after { background: var(--accent); }

.app-footer { display: flex; align-items: center; gap: 12px; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--gray-100); }
.text-muted { color: var(--gray-400); font-size: .75rem; }
.loading-center { display: flex; justify-content: center; padding: 4rem; }
</style>
