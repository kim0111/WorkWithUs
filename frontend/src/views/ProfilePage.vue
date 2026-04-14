<template>
  <div v-if="user" class="page container">
    <!-- Shared Header -->
    <div class="profile-header">
      <div class="profile-avatar">{{ (user.full_name || user.username)[0].toUpperCase() }}</div>
      <div class="profile-info">
        <div class="profile-name-row">
          <h1>{{ user.full_name || user.username }}</h1>
          <span class="badge" :class="roleBadge">{{ user.role }}</span>
        </div>
        <p class="profile-username">@{{ user.username }}</p>
        <div class="profile-meta">
          <span><span class="material-icons-round">email</span>{{ user.email }}</span>
          <span><span class="material-icons-round">calendar_today</span>Joined {{ fmtDate(user.created_at) }}</span>
          <span v-if="rating"><span class="material-icons-round">star</span>{{ rating.average_rating }}/5 ({{ rating.total_reviews }} reviews)</span>
        </div>
      </div>
      <button v-if="isMe" class="btn btn-secondary btn-sm" @click="showEdit = true">
        <span class="material-icons-round">edit</span>Edit
      </button>
      <button v-else-if="canInvite" class="btn btn-primary btn-sm" @click="showInvite = true">
        <span class="material-icons-round">person_add</span>Invite to Project
      </button>
    </div>

    <!-- Role-specific Info Grid -->
    <CompanyInfoGrid v-if="isCompany" :profile="roleProfile" :projectCount="projectCount" />
    <StudentInfoGrid v-if="isStudent" :profile="roleProfile" />

    <!-- Bio -->
    <p v-if="displayBio" class="profile-bio">{{ displayBio }}</p>

    <!-- Skills (student) -->
    <SkillPicker
      v-if="isStudent"
      :skills="user.skills || []"
      :userId="user.id"
      :editable="isMe"
      @updated="reload"
      class="profile-skills-section"
    />

    <!-- Tabs -->
    <BaseTabs :tabs="tabList" v-model="activeTab" />

    <!-- Tab Content -->
    <section class="tab-content">
      <!-- Company tabs -->
      <CompanyProjectsTab v-if="isCompany && activeTab === 'projects'" :userId="user.id" :isOwner="isMe" />
      <CompanyAppsTab v-if="isCompany && activeTab === 'applications' && isMe" :userId="user.id" />

      <!-- Student tabs -->
      <StudentPortfolioTab v-if="isStudent && activeTab === 'portfolio'" :portfolio="portfolio" :isOwner="isMe" @updated="reload" />
      <StudentAppsTab v-if="isStudent && activeTab === 'applications' && isMe" />

      <!-- Shared -->
      <ReviewsTab v-if="activeTab === 'reviews'" :reviews="reviews" />
    </section>

    <!-- Edit Modal -->
    <EditProfileModal
      v-model="showEdit"
      :user="user"
      :profile="roleProfile"
      :role="user.role"
      @saved="onSaved"
    />

    <InviteStudentModal v-if="user && canInvite" v-model="showInvite" :studentId="user.id" />
  </div>
  <div v-else class="loading-center"><div class="spinner"></div></div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usersAPI, portfolioAPI, reviewsAPI, projectsAPI } from '@/api'

import BaseTabs from '@/components/BaseTabs.vue'
import SkillPicker from '@/components/SkillPicker.vue'
import CompanyInfoGrid from '@/components/profile/CompanyInfoGrid.vue'
import StudentInfoGrid from '@/components/profile/StudentInfoGrid.vue'
import CompanyProjectsTab from '@/components/profile/CompanyProjectsTab.vue'
import CompanyAppsTab from '@/components/profile/CompanyAppsTab.vue'
import StudentPortfolioTab from '@/components/profile/StudentPortfolioTab.vue'
import StudentAppsTab from '@/components/profile/StudentAppsTab.vue'
import ReviewsTab from '@/components/profile/ReviewsTab.vue'
import EditProfileModal from '@/components/profile/EditProfileModal.vue'
import InviteStudentModal from '@/components/InviteStudentModal.vue'

const route = useRoute()
const auth = useAuthStore()

const user = ref(null)
const roleProfile = ref(null)
const portfolio = ref([])
const reviews = ref([])
const rating = ref(null)
const projectCount = ref(0)
const activeTab = ref('')
const showEdit = ref(false)
const showInvite = ref(false)

const isMe = computed(() => auth.user?.id === Number(route.params.id))
const isCompany = computed(() => user.value?.role === 'company')
const isStudent = computed(() => user.value?.role === 'student')
const canInvite = computed(() => auth.user?.role === 'company' && isStudent.value && !isMe.value)
const roleBadge = computed(() => ({
  student: 'badge-teal',
  company: 'badge-accent',
  admin: 'badge-danger',
  committee: 'badge-info',
}[user.value?.role]))

const displayBio = computed(() => {
  if (isCompany.value && roleProfile.value?.description) return roleProfile.value.description
  return user.value?.bio || ''
})

const tabList = computed(() => {
  if (isCompany.value) {
    const tabs = [
      { key: 'projects', label: 'Projects', count: projectCount.value },
    ]
    if (isMe.value) tabs.push({ key: 'applications', label: 'Applications' })
    tabs.push({ key: 'reviews', label: 'Reviews', count: rating.value?.total_reviews })
    return tabs
  }
  const tabs = [
    { key: 'portfolio', label: 'Portfolio', count: portfolio.value.length },
  ]
  if (isMe.value) tabs.push({ key: 'applications', label: 'Applications' })
  tabs.push({ key: 'reviews', label: 'Reviews', count: rating.value?.total_reviews })
  return tabs
})

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

async function reload() {
  await load()
}

async function onSaved() {
  await reload()
  await auth.fetchUser()
}

async function load() {
  const id = route.params.id
  try {
    user.value = (await usersAPI.get(id)).data
  } catch {
    return
  }

  // Load role-specific profile
  if (isCompany.value) {
    try { roleProfile.value = (await usersAPI.getCompanyProfile(id)).data } catch { roleProfile.value = null }
    try {
      const { data } = await projectsAPI.list({ owner_id: id, size: 1 })
      projectCount.value = data.total
    } catch { projectCount.value = 0 }
  } else if (isStudent.value) {
    try { roleProfile.value = (await usersAPI.getStudentProfile(id)).data } catch { roleProfile.value = null }
    try { portfolio.value = (await portfolioAPI.byUser(id)).data } catch { portfolio.value = [] }
  }

  try { reviews.value = (await reviewsAPI.forUser(id)).data } catch { reviews.value = [] }
  try { rating.value = (await reviewsAPI.rating(id)).data } catch { rating.value = null }

  // Set default tab
  if (!activeTab.value) {
    activeTab.value = isCompany.value ? 'projects' : 'portfolio'
  }
}

watch(() => route.params.id, () => {
  activeTab.value = ''
  load()
})

onMounted(load)
</script>

<style scoped>
.page {
  padding: 2rem 24px;
}
.profile-header {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  padding-bottom: 1.5rem;
}
.profile-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}
.profile-info {
  flex: 1;
}
.profile-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.profile-username {
  color: var(--gray-400);
  font-size: 0.8125rem;
  margin-top: 1px;
}
.profile-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
  font-size: 0.8125rem;
  color: var(--gray-400);
}
.profile-meta > span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.profile-meta .material-icons-round {
  font-size: 14px;
}
.profile-bio {
  margin-top: 12px;
  color: var(--gray-600);
  line-height: 1.6;
  font-size: 0.875rem;
  padding-bottom: 16px;
}
.profile-skills-section {
  margin: 16px 0;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--gray-200);
}
.loading-center {
  display: flex;
  justify-content: center;
  padding: 6rem;
}
@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .profile-meta {
    justify-content: center;
  }
  .profile-name-row {
    justify-content: center;
  }
}
</style>
