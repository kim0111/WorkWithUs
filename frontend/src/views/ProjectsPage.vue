<template>
  <div class="projects-page container">
    <header class="page-header">
      <div>
        <h1>Explore Projects</h1>
        <p class="page-subtitle">Find your next opportunity</p>
      </div>
      <router-link v-if="auth.isAuthenticated && (auth.isCompany || auth.isAdmin || auth.isStudent)"
        to="/projects/create" class="btn btn-primary">
        <span class="material-icons-round">add</span>
        New Project
      </router-link>
    </header>

    <!-- Filters -->
    <div class="filters-bar">
      <div class="search-box">
        <span class="material-icons-round">search</span>
        <input class="input" v-model="search" placeholder="Search projects..." @input="debouncedFetch" />
      </div>
      <select v-model="statusFilter" @change="fetchProjects" class="filter-select">
        <option value="">All Status</option>
        <option value="open">Open</option>
        <option value="in_progress">In Progress</option>
        <option value="closed">Closed</option>
      </select>
      <select v-model="typeFilter" @change="fetchProjects" class="filter-select">
        <option value="">All Types</option>
        <option value="false">Company</option>
        <option value="true">Student</option>
      </select>
    </div>

    <!-- Results -->
    <div v-if="loading" class="loading-page">
      <div class="spinner"></div>
    </div>

    <template v-else>
      <p class="results-count" v-if="total">{{ total }} project{{ total !== 1 ? 's' : '' }} found</p>

      <div v-if="projects.length" class="grid-2">
        <ProjectCard v-for="p in projects" :key="p.id" :project="p" />
      </div>

      <div v-else class="empty-state">
        <span class="material-icons-round">search_off</span>
        <h3>No projects found</h3>
        <p>Try adjusting your filters or search query.</p>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="goPage(page - 1)">
          <span class="material-icons-round">chevron_left</span>
        </button>
        <span class="page-info">{{ page }} / {{ totalPages }}</span>
        <button class="btn btn-ghost btn-sm" :disabled="page >= totalPages" @click="goPage(page + 1)">
          <span class="material-icons-round">chevron_right</span>
        </button>
      </div>
    </template>
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

let debounce = null
function debouncedFetch() {
  clearTimeout(debounce)
  debounce = setTimeout(() => { page.value = 1; fetchProjects() }, 350)
}

async function fetchProjects() {
  loading.value = true
  try {
    const params = { page: page.value, size }
    if (search.value) params.search = search.value
    if (statusFilter.value) params.status = statusFilter.value
    if (typeFilter.value !== '') params.is_student_project = typeFilter.value
    const { data } = await projectsAPI.list(params)
    projects.value = data.items
    total.value = data.total
  } catch { /* ignore */ }
  loading.value = false
}

function goPage(p) {
  page.value = p
  fetchProjects()
}

onMounted(fetchProjects)
</script>

<style scoped>
.projects-page {
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.page-subtitle {
  color: var(--text-secondary);
  margin-top: 4px;
}

.filters-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 240px;
}

.search-box .material-icons-round {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 20px;
}

.search-box .input {
  padding-left: 44px;
}

.filter-select {
  min-width: 150px;
}

.results-count {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border);
}

.page-info {
  font-size: 0.9rem;
  font-family: var(--font-mono);
  color: var(--text-secondary);
}
</style>
