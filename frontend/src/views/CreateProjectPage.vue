<template>
  <div class="create-project container">
    <button class="btn btn-ghost btn-sm" @click="$router.back()">
      <span class="material-icons-round">arrow_back</span> Back
    </button>

    <div class="form-card card">
      <h1>Create New Project</h1>
      <p class="form-subtitle">Fill in the details to publish your project</p>

      <form @submit.prevent="handleSubmit" class="project-form">
        <div class="input-group">
          <label>Project Title</label>
          <input class="input" v-model="form.title" placeholder="e.g. Build a mobile app for..." required />
        </div>

        <div class="input-group">
          <label>Description</label>
          <textarea v-model="form.description" placeholder="Describe the project in detail (min 10 chars)..." required></textarea>
        </div>

        <div class="row-2">
          <div class="input-group">
            <label>Max Participants</label>
            <input class="input" type="number" v-model.number="form.max_participants" min="1" max="100" />
          </div>
          <div class="input-group">
            <label>Deadline (Optional)</label>
            <input class="input" type="date" v-model="deadlineStr" />
          </div>
        </div>

        <div v-if="auth.isStudent" class="checkbox-row">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.is_student_project" />
            <span>This is a student-to-student project</span>
          </label>
        </div>

        <div class="input-group">
          <label>Required Skills</label>
          <div class="skills-select">
            <span
              v-for="s in allSkills" :key="s.id"
              class="skill-tag"
              :class="{ selected: form.skill_ids.includes(s.id) }"
              @click="toggleSkill(s.id)"
            >
              {{ s.name }}
              <span class="material-icons-round" v-if="form.skill_ids.includes(s.id)">check</span>
            </span>
          </div>
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button type="submit" class="btn btn-primary btn-lg" :disabled="submitting">
          {{ submitting ? 'Publishing...' : 'Publish Project' }}
          <span class="material-icons-round">send</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { projectsAPI, skillsAPI } from '@/api'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const allSkills = ref([])
const submitting = ref(false)
const errorMsg = ref('')
const deadlineStr = ref('')

const form = reactive({
  title: '',
  description: '',
  max_participants: 1,
  skill_ids: [],
  is_student_project: false,
})

function toggleSkill(id) {
  const idx = form.skill_ids.indexOf(id)
  if (idx >= 0) form.skill_ids.splice(idx, 1)
  else form.skill_ids.push(id)
}

async function handleSubmit() {
  errorMsg.value = ''
  submitting.value = true
  try {
    const payload = { ...form }
    if (deadlineStr.value) payload.deadline = new Date(deadlineStr.value).toISOString()
    const { data } = await projectsAPI.create(payload)
    toast.success('Project published!')
    router.push(`/projects/${data.id}`)
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Failed to create project'
  }
  submitting.value = false
}

onMounted(async () => {
  try {
    const { data } = await skillsAPI.list()
    allSkills.value = data
  } catch { /* ignore */ }
})
</script>

<style scoped>
.create-project {
  padding: 2rem;
  max-width: 720px;
}

.form-card {
  margin-top: 1.5rem;
}

.form-card h1 { margin-bottom: 6px; }
.form-subtitle { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 2rem; }

.project-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.checkbox-row {
  display: flex;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.9rem;
  cursor: pointer;
  color: var(--text-secondary);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--accent);
}

.skills-select {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skills-select .skill-tag {
  cursor: pointer;
  user-select: none;
}

.skills-select .skill-tag.selected {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-dim);
}

.skills-select .skill-tag .material-icons-round {
  font-size: 14px;
}

.error-msg {
  color: var(--danger);
  font-size: 0.85rem;
  background: rgba(248,113,113,0.08);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(248,113,113,0.15);
}

@media (max-width: 600px) {
  .row-2 { grid-template-columns: 1fr; }
}
</style>
