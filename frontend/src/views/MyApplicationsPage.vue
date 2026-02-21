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

        <!-- Status-specific info -->
        <p v-if="a.submission_note" class="status-note"><span class="material-icons-round">send</span>{{ a.submission_note }}</p>
        <p v-if="a.revision_note" class="status-note revision"><span class="material-icons-round">edit_note</span>{{ a.revision_note }}</p>

        <!-- Workflow progress -->
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
const apps = ref([]); const loading = ref(true)
const workflowSteps = ['pending', 'accepted', 'in_progress', 'submitted', 'approved', 'completed']
function stepIndex(s) { const i = workflowSteps.indexOf(s); return i >= 0 ? i : (s === 'rejected' ? -1 : s === 'revision_requested' ? 3 : 0) }
function statusBadge(s) {
  return { pending:'badge-info', accepted:'badge-success', rejected:'badge-danger', in_progress:'badge-warning',
    submitted:'badge-accent', revision_requested:'badge-warning', approved:'badge-success', completed:'badge-teal' }[s] || 'badge-info'
}
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US', { month:'short', day:'numeric' }) : '' }
onMounted(async () => { try { apps.value = (await applicationsAPI.my()).data } catch {} finally { loading.value = false } })
</script>
<style scoped>
.page { padding: 2rem; }
.apps-list { display: flex; flex-direction: column; gap: 16px; }
.app-card { padding: 24px; }
.app-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.app-project-link { display: flex; align-items: center; gap: 8px; text-decoration: none; color: var(--text-primary); font-weight: 600; font-size: 1.05rem; }
.app-project-link .material-icons-round { color: var(--accent); }
.app-letter { color: var(--text-secondary); font-size: .9rem; margin-bottom: 12px; line-height: 1.5; }
.status-note { display: flex; align-items: center; gap: 8px; font-size: .85rem; color: var(--text-secondary); padding: 8px 12px; background: var(--bg-secondary); border-radius: var(--radius-md); margin-bottom: 8px; }
.status-note.revision { color: var(--warning); background: rgba(251,191,36,.06); }
.status-note .material-icons-round { font-size: 18px; }

/* Workflow bar */
.workflow-bar { display: flex; gap: 0; margin: 16px 0; overflow-x: auto; }
.wf-step { display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1; min-width: 70px; position: relative; }
.wf-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--bg-card); border: 2px solid var(--border-strong); transition: all .2s; z-index: 1; }
.wf-step.done .wf-dot { background: var(--accent); border-color: var(--accent); }
.wf-step.current .wf-dot { background: var(--accent); border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-dim); }
.wf-label { font-size: .68rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em; text-align: center; }
.wf-step.done .wf-label, .wf-step.current .wf-label { color: var(--text-primary); font-weight: 600; }
.wf-step:not(:last-child)::after { content: ''; position: absolute; top: 5px; left: calc(50% + 8px); right: calc(-50% + 8px); height: 2px; background: var(--border-strong); }
.wf-step.done:not(:last-child)::after { background: var(--accent); }

.app-footer { display: flex; align-items: center; gap: 16px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); }
.text-muted { color: var(--text-muted); font-size: .82rem; }
.loading-center { display: flex; justify-content: center; padding: 4rem; }
</style>
