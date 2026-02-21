<template>
  <div class="page container">
    <header class="page-header"><h1>Create Project</h1></header>
    <form @submit.prevent="submit" class="create-form">
      <div class="input-group"><label>Title</label><input class="input" v-model="form.title" required minlength="3" placeholder="Project title" /></div>
      <div class="input-group"><label>Description</label><textarea class="input" v-model="form.description" rows="6" required minlength="10" placeholder="Detailed description..."></textarea></div>
      <div class="row2">
        <div class="input-group"><label>Max Participants</label><input class="input" type="number" v-model.number="form.max_participants" min="1" /></div>
        <div class="input-group"><label>Deadline</label><input class="input" type="datetime-local" v-model="form.deadline" /></div>
      </div>
      <div class="input-group">
        <label>Required Skills</label>
        <div class="skills-picker">
          <span v-for="s in allSkills" :key="s.id" class="skill-tag" :class="{ active: form.skill_ids.includes(s.id) }" @click="toggleSkill(s.id)">{{ s.name }}</span>
        </div>
      </div>
      <div v-if="auth.isStudent" class="checkbox-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="form.is_student_project" /><span>This is a student project (outsource)</span>
        </label>
      </div>
      <p v-if="err" class="error-msg">{{ err }}</p>
      <button type="submit" class="btn btn-primary btn-lg" :disabled="loading">{{ loading ? 'Creating...' : 'Create Project' }}</button>
    </form>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { projectsAPI, skillsAPI } from '@/api'
const router = useRouter(); const auth = useAuthStore(); const toast = useToastStore()
const loading = ref(false); const err = ref(''); const allSkills = ref([])
const form = reactive({ title: '', description: '', max_participants: 1, deadline: '', skill_ids: [], is_student_project: false })
function toggleSkill(id) { const i = form.skill_ids.indexOf(id); i >= 0 ? form.skill_ids.splice(i, 1) : form.skill_ids.push(id) }
async function submit() {
  err.value = ''; loading.value = true
  try {
    const payload = { ...form, deadline: form.deadline ? new Date(form.deadline).toISOString() : null }
    if (!auth.isStudent) payload.is_student_project = false
    const { data } = await projectsAPI.create(payload)
    toast.success('Project created!')
    router.push(`/projects/${data.id}`)
  } catch (e) { err.value = e.response?.data?.detail || 'Failed' }
  finally { loading.value = false }
}
onMounted(async () => { try { allSkills.value = (await skillsAPI.list()).data } catch {} })
</script>
<style scoped>
.page { padding: 2rem; }
.create-form { max-width: 700px; display: flex; flex-direction: column; gap: 20px; }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.skills-picker { display: flex; flex-wrap: wrap; gap: 8px; }
.skills-picker .skill-tag { cursor: pointer; transition: all .15s var(--ease); }
.skills-picker .skill-tag.active { background: var(--accent); color: var(--text-inverse); border-color: var(--accent); }
.checkbox-group { margin-top: -4px; }
.checkbox-label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: .9rem; color: var(--text-secondary); }
.checkbox-label input { width: 18px; height: 18px; accent-color: var(--accent); }
.error-msg { color: var(--danger); font-size: .85rem; background: rgba(248,113,113,.08); padding: 10px 14px; border-radius: var(--radius-md); border: 1px solid rgba(248,113,113,.15); }
@media (max-width: 768px) { .row2 { grid-template-columns: 1fr; } }
</style>
