<template>
  <router-link :to="`/projects/${project.id}`" class="project-card card card-interactive">
    <div class="card-header">
      <div class="card-meta">
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
      <span v-if="project.attachments?.length" class="footer-item"><span class="material-icons-round">attach_file</span>{{ project.attachments.length }} files</span>
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
.project-card{display:flex;flex-direction:column;gap:14px;text-decoration:none;color:inherit}
.card-header{display:flex;justify-content:space-between;align-items:center}.card-meta{display:flex;gap:6px}
.card-date{font-size:.78rem;color:var(--text-muted);font-family:var(--font-mono)}
.card-title{font-size:1.2rem;line-height:1.3}.card-desc{font-size:.9rem;color:var(--text-secondary);line-height:1.5}
.card-skills{display:flex;flex-wrap:wrap;gap:6px}
.card-footer{display:flex;gap:20px;padding-top:12px;border-top:1px solid var(--border);margin-top:auto}
.footer-item{display:flex;align-items:center;gap:5px;font-size:.82rem;color:var(--text-muted)}
.footer-item .material-icons-round{font-size:16px}
</style>
