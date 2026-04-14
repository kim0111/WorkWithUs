<template>
  <section class="detail-section">
    <div class="team-header">
      <h2>Team ({{ members.length }}/{{ maxParticipants }})</h2>
      <button v-if="canManage" class="btn btn-secondary btn-sm" @click="showAddModal = true">
        <span class="material-icons-round">person_add</span>Add Member
      </button>
      <button v-if="members.length >= 2" class="btn btn-ghost btn-sm" @click="openTeamChat">
        <span class="material-icons-round">forum</span>Team Chat
      </button>
    </div>

    <div v-if="members.length" class="team-list">
      <div v-for="m in members" :key="m.id" class="team-member">
        <router-link :to="`/profile/${m.user_id}`" class="member-info" @click.stop>
          <div class="av-sm">{{ (m.username || '?').charAt(0).toUpperCase() }}</div>
          <div class="member-detail">
            <span class="member-name">{{ m.full_name || m.username }}</span>
            <div class="member-meta">
              <span class="role-tag" :class="`role-${m.role}`">{{ m.role }}</span>
              <span v-if="m.is_lead" class="lead-badge">Lead</span>
            </div>
          </div>
        </router-link>
        <div v-if="canManage && !m.is_lead" class="member-actions">
          <select class="input select select-sm" :value="m.role" @change="changeRole(m, $event.target.value)">
            <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
          </select>
          <button class="btn btn-ghost btn-sm btn-danger-text" @click="confirmRemove(m)">
            <span class="material-icons-round">close</span>
          </button>
        </div>
        <div v-else-if="isSelf(m) && !m.is_lead" class="member-actions">
          <button class="btn btn-ghost btn-sm btn-danger-text" @click="confirmRemove(m)">
            <span class="material-icons-round">logout</span>Leave
          </button>
        </div>
      </div>
    </div>
    <EmptyState v-else icon="group" title="No team members yet" subtitle="Team members are added automatically when applications are accepted" />

    <!-- Add Member Modal -->
    <BaseModal v-model="showAddModal" title="Add Team Member">
      <form @submit.prevent="addMember" class="add-form">
        <FormField label="User ID">
          <input class="input" v-model.number="addUserId" type="number" placeholder="Enter user ID" required />
        </FormField>
        <FormField label="Role">
          <select class="input select" v-model="addRole">
            <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
          </select>
        </FormField>
        <button type="submit" class="btn btn-primary" :disabled="adding">
          {{ adding ? 'Adding...' : 'Add to Team' }}
        </button>
      </form>
    </BaseModal>

    <ConfirmDialog
      v-model="showRemoveConfirm"
      title="Remove Team Member"
      :message="removeMsg"
      @confirm="doRemove"
    />
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTeamsStore } from '@/stores/teams'
import { useToastStore } from '@/stores/toast'
import { teamsAPI } from '@/api'
import BaseModal from '@/components/BaseModal.vue'
import FormField from '@/components/FormField.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'

const props = defineProps({
  projectId: { type: Number, required: true },
  maxParticipants: { type: Number, default: 5 },
  isOwner: { type: Boolean, default: false },
})

const auth = useAuthStore()
const teamsStore = useTeamsStore()
const toast = useToastStore()
const router = useRouter()

const roles = ['lead', 'frontend', 'backend', 'designer', 'pm', 'qa', 'other']
const showAddModal = ref(false)
const showRemoveConfirm = ref(false)
const addUserId = ref(null)
const addRole = ref('other')
const adding = ref(false)
const removingMember = ref(null)

const members = computed(() => teamsStore.byProject[props.projectId] || [])
const canManage = computed(() => {
  if (props.isOwner || auth.isAdmin) return true
  return members.value.some(m => m.user_id === auth.user?.id && m.is_lead)
})

const removeMsg = computed(() => {
  if (!removingMember.value) return ''
  if (removingMember.value.user_id === auth.user?.id) return 'Are you sure you want to leave this team?'
  return `Remove ${removingMember.value.full_name || removingMember.value.username} from the team?`
})

function isSelf(m) {
  return m.user_id === auth.user?.id
}

async function addMember() {
  adding.value = true
  try {
    await teamsStore.addMember(props.projectId, { user_id: addUserId.value, role: addRole.value })
    toast.success('Member added')
    showAddModal.value = false
    addUserId.value = null
    addRole.value = 'other'
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to add member')
  } finally {
    adding.value = false
  }
}

async function changeRole(member, newRole) {
  try {
    await teamsStore.updateMember(props.projectId, member.user_id, { role: newRole })
    toast.success('Role updated')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to update role')
  }
}

function confirmRemove(member) {
  removingMember.value = member
  showRemoveConfirm.value = true
}

async function doRemove() {
  showRemoveConfirm.value = false
  if (!removingMember.value) return
  try {
    await teamsStore.removeMember(props.projectId, removingMember.value.user_id)
    toast.success('Member removed')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to remove member')
  }
  removingMember.value = null
}

async function openTeamChat() {
  try {
    const { data } = await teamsAPI.teamRoom(props.projectId)
    router.push(`/chat/${data.id}`)
  } catch {
    toast.error('Cannot open team chat')
  }
}
</script>

<style scoped>
.team-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: .75rem;
}
.team-header h2 { margin-bottom: 0; font-size: 1.1rem; flex: 1; }

.team-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.team-member {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
}

.member-info {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
  flex: 1;
  min-width: 0;
}

.av-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: .75rem;
  color: white;
  flex-shrink: 0;
}

.member-detail { min-width: 0; }
.member-name {
  font-weight: 500;
  font-size: .875rem;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.member-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
}

.role-tag {
  font-size: .6875rem;
  padding: 1px 8px;
  border-radius: var(--radius-full);
  background: var(--gray-100);
  color: var(--gray-600);
  text-transform: capitalize;
}
.role-lead { background: var(--accent-light, #e0f2fe); color: var(--accent); }
.role-frontend { background: #fef3c7; color: #92400e; }
.role-backend { background: #dbeafe; color: #1e40af; }
.role-designer { background: #fce7f3; color: #9d174d; }
.role-pm { background: #e0e7ff; color: #3730a3; }
.role-qa { background: #d1fae5; color: #065f46; }

.lead-badge {
  font-size: .6875rem;
  padding: 1px 8px;
  border-radius: var(--radius-full);
  background: var(--warning-light, #fef3c7);
  color: var(--warning, #d97706);
  font-weight: 600;
}

.member-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.select-sm {
  font-size: .75rem;
  padding: 4px 8px;
  min-width: 90px;
}

.btn-danger-text { color: var(--danger); }
.btn-danger-text:hover { background: var(--danger-light, #fee2e2); }

.add-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (max-width: 640px) {
  .team-member { flex-direction: column; align-items: flex-start; }
  .member-actions { width: 100%; justify-content: flex-end; }
}
</style>
