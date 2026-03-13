<template>
  <router-link :to="`/projects/${project.id}`" class="project-card card card-interactive">
    <div class="card-top">
      <div class="card-badges">
        <span class="badge" :class="statusClass">{{ project.status }}</span>
        <span v-if="project.is_student_project" class="badge badge-teal">Student</span>
      </div>
      <span class="card-date">{{ fmtDate(project.created_at) }}</span>
    </div>
    <h3 class="card-title">{{ project.title }}</h3>
    <p class="card-desc">{{ project.description?.length > 120 ? project.description.slice(0,120) + '...' : project.description }}</p>
    <div v-if="project.required_skills?.length" class="card-skills">
      <span v-for="s in project.required_skills.slice(0,4)" :key="s.id" class="skill-tag">{{ s.name }}</span>
      <span v-if="project.required_skills.length > 4" class="skill-tag">+{{ project.required_skills.length - 4 }}</span>
    </div>
    <div class="card-footer">
      <span class="footer-item"><span class="material-icons-round">group</span>{{ project.max_participants }} spots</span>
      <span v-if="project.deadline" class="footer-item"><span class="material-icons-round">schedule</span>{{ fmtDate(project.deadline) }}</span>
    </div>
  </router-link>
</template>
<script setup>
import { computed } from 'vue'
const p = defineProps({ project: Object })
const statusClass = computed(() => ({ open:'badge-success', in_progress:'badge-warning', closed:'badge-danger' }[p.project.status] || 'badge-info'))
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}) : '' }
</script>
<style scoped>
.project-card { display: flex; flex-direction: column; gap: 10px; text-decoration: none; color: inherit; min-width: 0; overflow: hidden; }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.card-badges { display: flex; gap: 6px; }
.card-date { font-size: .75rem; color: var(--gray-400); }
.card-title { font-size: 1rem; line-height: 1.4; color: var(--gray-900); overflow-wrap: break-word; word-break: break-word; }
.card-desc { font-size: .8125rem; color: var(--gray-500); line-height: 1.5; overflow-wrap: break-word; word-break: break-word; }
.card-skills { display: flex; flex-wrap: wrap; gap: 4px; }
.card-footer { display: flex; gap: 16px; padding-top: 10px; border-top: 1px solid var(--gray-100); margin-top: auto; }
.footer-item { display: flex; align-items: center; gap: 4px; font-size: .75rem; color: var(--gray-400); }
.footer-item .material-icons-round { font-size: 14px; }
</style>
