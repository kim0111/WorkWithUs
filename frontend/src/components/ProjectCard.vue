<template>
  <router-link :to="`/projects/${project.id}`" class="project-card card card-interactive">
    <div class="card-header">
      <div class="card-meta">
        <span class="badge" :class="statusBadge">{{ project.status }}</span>
        <span v-if="project.is_student_project" class="badge badge-teal">Student</span>
      </div>
      <span class="card-date">{{ formatDate(project.created_at) }}</span>
    </div>

    <h3 class="card-title">{{ project.title }}</h3>
    <p class="card-desc">{{ truncate(project.description, 120) }}</p>

    <div v-if="project.required_skills?.length" class="card-skills">
      <span v-for="skill in project.required_skills.slice(0, 4)" :key="skill.id" class="skill-tag">
        {{ skill.name }}
      </span>
      <span v-if="project.required_skills.length > 4" class="skill-tag">
        +{{ project.required_skills.length - 4 }}
      </span>
    </div>

    <div class="card-footer">
      <div class="footer-item">
        <span class="material-icons-round">group</span>
        {{ project.max_participants }} spots
      </div>
      <div v-if="project.deadline" class="footer-item">
        <span class="material-icons-round">schedule</span>
        {{ formatDate(project.deadline) }}
      </div>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  project: { type: Object, required: true }
})

const statusBadge = computed(() => {
  const map = { open: 'badge-success', in_progress: 'badge-warning', closed: 'badge-danger' }
  return map[props.project.status] || 'badge-info'
})

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function truncate(s, n) {
  if (!s) return ''
  return s.length > n ? s.slice(0, n) + '...' : s
}
</script>

<style scoped>
.project-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  text-decoration: none;
  color: inherit;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-meta {
  display: flex;
  gap: 6px;
}

.card-date {
  font-size: 0.78rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.card-title {
  font-size: 1.2rem;
  line-height: 1.3;
}

.card-desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.card-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.card-footer {
  display: flex;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  margin-top: auto;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.82rem;
  color: var(--text-muted);
}

.footer-item .material-icons-round {
  font-size: 16px;
}
</style>
