<template>
  <div class="page container">
    <header class="page-header">
      <div>
        <h1>Projects</h1>
        <p class="page-sub">{{ store.total }} projects available</p>
      </div>
      <router-link v-if="auth.isAuth" to="/projects/create" class="btn btn-primary">
        <span class="material-icons-round">add</span>New Project
      </router-link>
    </header>

    <div class="filters-bar">
      <div class="search-box">
        <span class="material-icons-round">search</span>
        <input class="input" v-model="search" placeholder="Search projects..." @input="debouncedFetch" />
      </div>
      <div class="filter-group">
        <select class="input select" v-model="statusFilter" @change="resetAndFetch">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="closed">Closed</option>
        </select>
        <select class="input select" v-model="typeFilter" @change="resetAndFetch">
          <option value="">All Types</option>
          <option value="false">Company</option>
          <option value="true">Student</option>
        </select>
        <select class="input select" v-model="sortBy" @change="resetAndFetch">
          <option value="newest">Newest</option>
          <option value="deadline">Deadline</option>
        </select>
        <button
          v-if="auth.isStudent && auth.user?.skills?.length"
          class="match-btn"
          :class="{ 'match-active': matchSkills }"
          :aria-pressed="matchSkills"
          @click="toggleMatchSkills"
        >
          <span class="material-icons-round" aria-hidden="true">auto_awesome</span>
          Match My Skills
        </button>
      </div>
    </div>

    <div v-if="store.loading" class="projects-grid">
      <div v-for="n in 6" :key="n" class="card" style="display: flex; flex-direction: column; gap: 12px;">
        <SkeletonBlock height="20px" width="70%" />
        <SkeletonBlock height="14px" width="40%" />
        <SkeletonBlock height="60px" />
        <div style="display: flex; gap: 6px;">
          <SkeletonBlock height="22px" width="60px" border-radius="var(--radius-full)" />
          <SkeletonBlock height="22px" width="80px" border-radius="var(--radius-full)" />
        </div>
      </div>
    </div>
    <div v-else-if="store.items.length" class="projects-grid">
      <ProjectCard v-for="p in store.items" :key="p.id" :project="p" />
    </div>
    <div v-else class="empty-state">
      <span class="material-icons-round">folder_open</span>
      <h3>No projects found</h3>
      <p>Try adjusting your filters or search query</p>
    </div>

    <div v-if="totalPages > 1" class="pagination">
      <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="page--; fetchProjects()">
        <span class="material-icons-round">chevron_left</span>
      </button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn btn-ghost btn-sm" :disabled="page >= totalPages" @click="page++; fetchProjects()">
        <span class="material-icons-round">chevron_right</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectsStore } from '@/stores/projects'
import ProjectCard from '@/components/ProjectCard.vue'
import SkeletonBlock from '@/components/SkeletonBlock.vue'

const auth = useAuthStore()
const store = useProjectsStore()
const page = ref(1)
const size = 12
const search = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const sortBy = ref('newest')
const matchSkills = ref(false)
const totalPages = computed(() => Math.ceil(store.total / size))

let timer
function debouncedFetch() { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; fetchProjects() }, 300) }
onUnmounted(() => clearTimeout(timer))

function resetAndFetch() {
  page.value = 1
  fetchProjects()
}

function toggleMatchSkills() {
  matchSkills.value = !matchSkills.value
  resetAndFetch()
}

async function fetchProjects() {
  const params = { page: page.value, size }
  if (search.value) params.search = search.value
  if (statusFilter.value) params.status = statusFilter.value
  if (typeFilter.value !== '') params.is_student_project = typeFilter.value === 'true'
  if (sortBy.value !== 'newest') params.sort = sortBy.value
  if (matchSkills.value && auth.user?.skills?.length) {
    params.skill_ids = auth.user.skills.map(s => s.id)
  }
  await store.fetchList(params)
}

onMounted(fetchProjects)
</script>

<style scoped>
.page { padding: 2rem 24px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
.page-sub { color: var(--gray-400); font-size: .8125rem; margin-top: 2px; }
.filters-bar { display: flex; gap: 10px; margin-bottom: 1.5rem; flex-wrap: wrap; }
.search-box { flex: 1; min-width: 220px; position: relative; display: flex; align-items: center; }
.search-box .material-icons-round { position: absolute; left: 12px; color: var(--gray-400); font-size: 18px; }
.search-box .input { padding-left: 36px; width: 100%; }
.filter-group { display: flex; gap: 8px; flex-wrap: wrap; }
.select { min-width: 140px; }
.projects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 1.5rem; }
.page-info { font-size: .8125rem; color: var(--gray-500); }
.match-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  background: var(--white);
  font-size: .8125rem;
  cursor: pointer;
  transition: all .15s ease;
  white-space: nowrap;
}
.match-btn:hover { border-color: var(--gray-300); }
.match-btn .material-icons-round { font-size: 16px; }
.match-active {
  background: var(--accent);
  color: var(--white);
  border-color: var(--accent);
}
.match-active:hover { opacity: 0.9; }
</style>
