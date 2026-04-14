<template>
  <div class="page container">
    <header class="page-header">
      <div>
        <h1>Students</h1>
        <p class="page-sub">{{ total }} students {{ availableOnly ? 'available' : 'registered' }}</p>
      </div>
    </header>

    <div class="filters-bar">
      <div class="search-box">
        <span class="material-icons-round">search</span>
        <input class="input" v-model="q" placeholder="Search by name or username..." @input="debouncedFetch" />
      </div>
      <div class="filter-group">
        <input class="input" type="number" v-model.number="minRating" step="0.5" min="0" max="5"
               placeholder="Min rating" style="width:120px" @change="resetAndFetch" />
        <label class="avail-toggle">
          <input type="checkbox" v-model="availableOnly" @change="resetAndFetch" />
          Available only
        </label>
      </div>
    </div>

    <div class="skills-filter">
      <SkillPicker :skills="selectedSkills" :editable="true"
                   :userId="null" @updated="onSkillsUpdate" />
    </div>

    <div v-if="loading" class="grid">
      <div v-for="n in 6" :key="n" class="card">
        <SkeletonBlock height="18px" width="60%" />
        <div style="margin-top:10px"><SkeletonBlock height="12px" width="40%" /></div>
      </div>
    </div>
    <div v-else-if="students.length" class="grid">
      <router-link v-for="s in students" :key="s.id"
                   :to="`/profile/${s.id}`" class="student-card card">
        <div class="student-head">
          <div class="student-avatar">{{ (s.full_name || s.username)[0].toUpperCase() }}</div>
          <div class="student-info">
            <div class="student-name">{{ s.full_name || s.username }}</div>
            <div class="student-meta">
              <span v-if="s.rating">⭐ {{ s.rating.toFixed(1) }}</span>
              <span>· {{ s.completed_projects_count }} completed</span>
              <span v-if="s.is_available" class="avail-chip">Available</span>
            </div>
          </div>
        </div>
        <div v-if="s.skills?.length" class="skills-row">
          <span v-for="sk in s.skills.slice(0,4)" :key="sk.id" class="skill-chip">{{ sk.name }}</span>
          <span v-if="s.skills.length > 4" class="skill-chip">+{{ s.skills.length - 4 }}</span>
        </div>
        <button class="btn btn-primary btn-sm invite-btn" @click.prevent.stop="openInvite(s)">
          <span class="material-icons-round">person_add</span>Invite
        </button>
      </router-link>
    </div>
    <EmptyState v-else icon="search_off" title="No students match" subtitle="Adjust the filters to see more." />

    <div v-if="totalPages > 1" class="pagination">
      <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="page--; fetch()">
        <span class="material-icons-round">chevron_left</span>
      </button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn btn-ghost btn-sm" :disabled="page >= totalPages" @click="page++; fetch()">
        <span class="material-icons-round">chevron_right</span>
      </button>
    </div>

    <InviteStudentModal v-if="inviteTarget" v-model="inviteOpen" :studentId="inviteTarget.id" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { usersAPI } from '@/api'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'
import SkillPicker from '@/components/SkillPicker.vue'
import InviteStudentModal from '@/components/InviteStudentModal.vue'

const students = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 12
const q = ref('')
const minRating = ref(null)
const availableOnly = ref(false)
const selectedSkills = ref([])

const inviteOpen = ref(false)
const inviteTarget = ref(null)

const totalPages = computed(() => Math.ceil(total.value / size))

function openInvite(student) {
  inviteTarget.value = student
  inviteOpen.value = true
}

function onSkillsUpdate(skills) {
  selectedSkills.value = skills || []
  resetAndFetch()
}

let timer
function debouncedFetch() {
  clearTimeout(timer)
  timer = setTimeout(() => { page.value = 1; fetch() }, 300)
}
onUnmounted(() => clearTimeout(timer))

function resetAndFetch() {
  page.value = 1
  fetch()
}

async function fetch() {
  loading.value = true
  const params = { page: page.value, size }
  if (q.value) params.q = q.value
  if (minRating.value !== null && minRating.value !== '') params.min_rating = minRating.value
  if (availableOnly.value) params.available = true
  if (selectedSkills.value.length) params.skills = selectedSkills.value.map(s => s.id)
  try {
    const { data } = await usersAPI.search(params)
    students.value = data.items
    total.value = data.total
  } catch {
    students.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
</script>

<style scoped>
.page { padding: 2rem 24px; }
.page-header { margin-bottom: 1.5rem; }
.page-sub { color: var(--gray-400); font-size: .8125rem; margin-top: 2px; }
.filters-bar { display: flex; gap: 10px; margin-bottom: 1rem; flex-wrap: wrap; }
.search-box { flex: 1; min-width: 220px; position: relative; display: flex; align-items: center; }
.search-box .material-icons-round { position: absolute; left: 12px; color: var(--gray-400); font-size: 18px; }
.search-box .input { padding-left: 36px; width: 100%; }
.filter-group { display: flex; align-items: center; gap: 10px; }
.avail-toggle { display: flex; align-items: center; gap: 6px; font-size: .8125rem; color: var(--gray-600); }
.skills-filter { margin-bottom: 1.5rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.student-card {
  padding: 16px; text-decoration: none; color: inherit;
  display: flex; flex-direction: column; gap: 12px;
  border: 1px solid var(--gray-200); border-radius: var(--radius-lg); background: var(--white);
  transition: all .15s ease;
}
.student-card:hover { border-color: var(--gray-300); box-shadow: var(--shadow-sm); }
.student-head { display: flex; gap: 12px; align-items: center; }
.student-avatar {
  width: 44px; height: 44px; border-radius: 50%; background: var(--accent); color: white;
  display: flex; align-items: center; justify-content: center; font-weight: 600;
}
.student-info { flex: 1; min-width: 0; }
.student-name { font-weight: 600; color: var(--gray-900); font-size: .9375rem; }
.student-meta { display: flex; flex-wrap: wrap; gap: 8px; font-size: .75rem; color: var(--gray-500); margin-top: 2px; }
.avail-chip { background: #dcfce7; color: #166534; padding: 1px 8px; border-radius: 12px; }
.skills-row { display: flex; gap: 6px; flex-wrap: wrap; }
.skill-chip { background: var(--gray-100); color: var(--gray-700); padding: 2px 8px; border-radius: 12px; font-size: .75rem; }
.invite-btn { justify-content: center; margin-top: auto; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 1.5rem; }
.page-info { font-size: .8125rem; color: var(--gray-500); }
</style>
