<template>
  <div class="page container">
    <header class="page-header">
      <div>
        <h1>Projects</h1>
        <p class="page-sub">{{ total }} projects available</p>
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
        <select class="input select" v-model="statusFilter" @change="fetchProjects">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="closed">Closed</option>
        </select>
        <select class="input select" v-model="typeFilter" @change="fetchProjects">
          <option value="">All Types</option>
          <option value="false">Company</option>
          <option value="true">Student</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="projects.length" class="projects-grid">
      <ProjectCard v-for="p in projects" :key="p.id" :project="p" />
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
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { projectsAPI } from '@/api'
import ProjectCard from '@/components/ProjectCard.vue'

const auth = useAuthStore()
const projects = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const size = 12
const search = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const totalPages = computed(() => Math.ceil(total.value / size))

let timer
function debouncedFetch() { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; fetchProjects() }, 300) }

async function fetchProjects() {
  loading.value = true
  try {
    const params = { page: page.value, size }
    if (search.value) params.search = search.value
    if (statusFilter.value) params.status = statusFilter.value
    if (typeFilter.value !== '') params.is_student_project = typeFilter.value === 'true'
    const { data } = await projectsAPI.list(params)
    projects.value = data.items
    total.value = data.total
  } catch {} finally { loading.value = false }
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
.filter-group { display: flex; gap: 8px; }
.select { min-width: 140px; }
.projects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 1.5rem; }
.page-info { font-size: .8125rem; color: var(--gray-500); }
.loading-center { display: flex; justify-content: center; padding: 4rem; }
</style>
