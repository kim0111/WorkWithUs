<template>
  <BaseModal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)"
             title="Invite to Project" maxWidth="480px">
    <div v-if="loading" class="loading-msg">Loading your projects...</div>
    <div v-else-if="!projects.length" class="empty-msg">
      <p>You have no open projects yet.</p>
      <router-link to="/projects/create" class="btn btn-primary btn-sm" @click="close">
        Create a Project
      </router-link>
    </div>
    <form v-else @submit.prevent="submit" class="invite-form">
      <FormField label="Project" :error="projectError">
        <select v-model="selectedProject" class="input select" required>
          <option value="" disabled>Choose one of your open projects</option>
          <option v-for="p in projects" :key="p.id" :value="p.id" :disabled="isFull(p)">
            {{ p.title }}{{ isFull(p) ? ' (full)' : '' }}
          </option>
        </select>
      </FormField>
      <FormField label="Message (optional)" hint="Will be shown to the student">
        <textarea class="input" v-model="message" rows="4"
                  placeholder="Tell them why you'd like them on this project..." maxlength="2000"></textarea>
      </FormField>
      <p v-if="errorMsg" class="invite-error">{{ errorMsg }}</p>
    </form>
    <template #footer>
      <button class="btn btn-ghost btn-sm" @click="close" :disabled="busy">Cancel</button>
      <button v-if="projects.length" class="btn btn-primary btn-sm"
              :disabled="!selectedProject || busy" @click="submit">
        {{ busy ? 'Sending...' : 'Send Invitation' }}
      </button>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useApplicationsStore } from '@/stores/applications'
import { projectsAPI } from '@/api'
import BaseModal from '@/components/BaseModal.vue'
import FormField from '@/components/FormField.vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  studentId: { type: Number, required: true },
})
const emit = defineEmits(['update:modelValue', 'sent'])

const auth = useAuthStore()
const applications = useApplicationsStore()
const loading = ref(false)
const busy = ref(false)
const projects = ref([])
const selectedProject = ref('')
const message = ref('')
const errorMsg = ref('')
const projectError = computed(() => '')

async function loadProjects() {
  if (!auth.user?.id) return
  loading.value = true
  try {
    const { data } = await projectsAPI.list({
      owner_id: auth.user.id, status: 'open', size: 50,
    })
    projects.value = data.items || []
  } catch {
    projects.value = []
  } finally {
    loading.value = false
  }
}

function isFull(p) {
  return typeof p.active_count === 'number' && p.active_count >= p.max_participants
}

async function submit() {
  if (!selectedProject.value) return
  busy.value = true
  errorMsg.value = ''
  try {
    await applications.invite({
      project_id: selectedProject.value,
      student_id: props.studentId,
      message: message.value || null,
    })
    emit('sent')
    reset()
    close()
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Could not send invitation.'
  } finally {
    busy.value = false
  }
}

function reset() {
  selectedProject.value = ''
  message.value = ''
  errorMsg.value = ''
}

function close() {
  if (busy.value) return
  emit('update:modelValue', false)
}

watch(() => props.modelValue, (open) => {
  if (open) {
    reset()
    loadProjects()
  }
})
</script>

<style scoped>
.invite-form { display: flex; flex-direction: column; gap: 14px; }
.loading-msg, .empty-msg { padding: 16px; text-align: center; color: var(--gray-500); font-size: .8125rem; }
.empty-msg .btn { margin-top: 10px; }
.invite-error {
  color: var(--danger); font-size: .8125rem;
  background: var(--danger-light); padding: 8px 12px;
  border-radius: var(--radius-md); margin: 0;
}
.input.select { width: 100%; }
</style>
