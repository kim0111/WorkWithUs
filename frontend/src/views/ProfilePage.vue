<template>
  <div v-if="loading" class="loading-page"><div class="spinner"></div></div>

  <div v-else-if="user" class="profile-page container">
    <!-- Profile header -->
    <div class="profile-header card">
      <div class="profile-avatar">{{ initial }}</div>
      <div class="profile-info">
        <div class="profile-name-row">
          <h1>{{ user.full_name || user.username }}</h1>
          <span class="badge" :class="roleBadge">{{ user.role }}</span>
        </div>
        <p class="profile-username">@{{ user.username }}</p>
        <p v-if="user.bio" class="profile-bio">{{ user.bio }}</p>

        <div class="profile-meta">
          <span class="meta-chip">
            <span class="material-icons-round">email</span>
            {{ user.email }}
          </span>
          <span class="meta-chip">
            <span class="material-icons-round">calendar_today</span>
            Joined {{ formatDate(user.created_at) }}
          </span>
          <span v-if="avgRating" class="meta-chip">
            <span class="material-icons-round">star</span>
            {{ avgRating.toFixed(1) }} rating
          </span>
        </div>

        <div v-if="user.skills?.length" class="profile-skills">
          <span v-for="s in user.skills" :key="s.id" class="skill-tag">{{ s.name }}</span>
        </div>
      </div>

      <button v-if="isOwn" class="btn btn-outline btn-sm edit-btn" @click="showEdit = true">
        <span class="material-icons-round">edit</span> Edit Profile
      </button>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button v-for="t in tabs" :key="t.key" class="tab" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
        <span class="material-icons-round">{{ t.icon }}</span>
        {{ t.label }}
      </button>
    </div>

    <!-- Portfolio tab -->
    <div v-if="activeTab === 'portfolio'">
      <div class="tab-header">
        <h2>Portfolio</h2>
        <button v-if="isOwn" class="btn btn-primary btn-sm" @click="showAddPortfolio = true">
          <span class="material-icons-round">add</span> Add Item
        </button>
      </div>
      <div v-if="portfolio.length" class="grid-2">
        <div v-for="item in portfolio" :key="item.id" class="card portfolio-item">
          <h4>{{ item.title }}</h4>
          <p v-if="item.description">{{ item.description }}</p>
          <a v-if="item.project_url" :href="item.project_url" target="_blank" class="portfolio-link">
            <span class="material-icons-round">link</span> View Project
          </a>
          <button v-if="isOwn" class="btn btn-ghost btn-sm" @click="deletePortfolio(item.id)">
            <span class="material-icons-round">delete</span>
          </button>
        </div>
      </div>
      <div v-else class="empty-state">
        <span class="material-icons-round">collections</span>
        <h3>No portfolio items</h3>
        <p>{{ isOwn ? 'Add your first project to showcase your work.' : 'This user hasn\'t added portfolio items yet.' }}</p>
      </div>
    </div>

    <!-- Reviews tab -->
    <div v-if="activeTab === 'reviews'">
      <h2 style="margin-bottom: 1rem">Reviews</h2>
      <div v-if="reviews.length" class="reviews-list">
        <div v-for="r in reviews" :key="r.id" class="card review-item">
          <div class="review-top">
            <div class="review-stars">
              <span v-for="i in 5" :key="i" class="material-icons-round" :class="{ filled: i <= r.rating }">star</span>
            </div>
            <span class="review-date">{{ formatDate(r.created_at) }}</span>
          </div>
          <p v-if="r.comment">{{ r.comment }}</p>
        </div>
      </div>
      <div v-else class="empty-state">
        <span class="material-icons-round">rate_review</span>
        <h3>No reviews yet</h3>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEdit" class="modal-overlay" @click.self="showEdit = false">
      <div class="modal">
        <h2>Edit Profile</h2>
        <p class="modal-subtitle">Update your public profile information</p>
        <form @submit.prevent="saveProfile" class="auth-form" style="display:flex;flex-direction:column;gap:16px">
          <div class="input-group">
            <label>Full Name</label>
            <input class="input" v-model="editForm.full_name" />
          </div>
          <div class="input-group">
            <label>Bio</label>
            <textarea v-model="editForm.bio" placeholder="Tell us about yourself..."></textarea>
          </div>
          <div style="display:flex;gap:10px;justify-content:flex-end">
            <button type="button" class="btn btn-ghost" @click="showEdit = false">Cancel</button>
            <button type="submit" class="btn btn-primary">Save Changes</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Add Portfolio Modal -->
    <div v-if="showAddPortfolio" class="modal-overlay" @click.self="showAddPortfolio = false">
      <div class="modal">
        <h2>Add Portfolio Item</h2>
        <p class="modal-subtitle">Showcase your work</p>
        <form @submit.prevent="addPortfolioItem" style="display:flex;flex-direction:column;gap:16px">
          <div class="input-group">
            <label>Title</label>
            <input class="input" v-model="portfolioForm.title" required />
          </div>
          <div class="input-group">
            <label>Description</label>
            <textarea v-model="portfolioForm.description" placeholder="Describe your work..."></textarea>
          </div>
          <div class="input-group">
            <label>Project URL</label>
            <input class="input" v-model="portfolioForm.project_url" placeholder="https://..." />
          </div>
          <div style="display:flex;gap:10px;justify-content:flex-end">
            <button type="button" class="btn btn-ghost" @click="showAddPortfolio = false">Cancel</button>
            <button type="submit" class="btn btn-primary">Add Item</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { usersAPI, portfolioAPI, reviewsAPI } from '@/api'

const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const user = ref(null)
const portfolio = ref([])
const reviews = ref([])
const avgRating = ref(null)
const loading = ref(true)
const activeTab = ref('portfolio')
const showEdit = ref(false)
const showAddPortfolio = ref(false)

const editForm = reactive({ full_name: '', bio: '' })
const portfolioForm = reactive({ title: '', description: '', project_url: '' })

const isOwn = computed(() => auth.user?.id === user.value?.id)
const initial = computed(() => (user.value?.full_name || user.value?.username || 'U')[0].toUpperCase())

const roleBadge = computed(() => {
  const m = { student: 'badge-teal', company: 'badge-accent', admin: 'badge-danger', committee: 'badge-info' }
  return m[user.value?.role] || 'badge-info'
})

const tabs = computed(() => {
  const t = [{ key: 'portfolio', label: 'Portfolio', icon: 'collections' }]
  t.push({ key: 'reviews', label: 'Reviews', icon: 'star' })
  return t
})

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

async function saveProfile() {
  try {
    const { data } = await usersAPI.update(user.value.id, editForm)
    user.value.full_name = data.full_name
    user.value.bio = data.bio
    showEdit.value = false
    toast.success('Profile updated!')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to update')
  }
}

async function addPortfolioItem() {
  try {
    const { data } = await portfolioAPI.add(portfolioForm)
    portfolio.value.push(data)
    showAddPortfolio.value = false
    portfolioForm.title = ''
    portfolioForm.description = ''
    portfolioForm.project_url = ''
    toast.success('Portfolio item added!')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to add')
  }
}

async function deletePortfolio(id) {
  try {
    await portfolioAPI.delete(id)
    portfolio.value = portfolio.value.filter(p => p.id !== id)
    toast.success('Item removed')
  } catch { toast.error('Failed to remove') }
}

onMounted(async () => {
  const userId = route.params.id
  try {
    const { data } = await usersAPI.get(userId)
    user.value = data
    editForm.full_name = data.full_name || ''
    editForm.bio = data.bio || ''

    const [portRes, revRes, ratingRes] = await Promise.allSettled([
      portfolioAPI.getByUser(userId),
      reviewsAPI.getForUser(userId),
      reviewsAPI.getRating(userId),
    ])
    if (portRes.status === 'fulfilled') portfolio.value = portRes.value.data
    if (revRes.status === 'fulfilled') reviews.value = revRes.value.data
    if (ratingRes.status === 'fulfilled') avgRating.value = ratingRes.value.data.average_rating
  } catch { /* ignore */ }
  loading.value = false
})
</script>

<style scoped>
.profile-page { padding: 2rem; }

.profile-header {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  margin-bottom: 2rem;
  position: relative;
}

.profile-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #d4822a);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-inverse);
  flex-shrink: 0;
}

.profile-info { flex: 1; }
.profile-name-row { display: flex; align-items: center; gap: 12px; margin-bottom: 2px; }
.profile-username { font-size: 0.9rem; color: var(--text-muted); font-family: var(--font-mono); margin-bottom: 8px; }
.profile-bio { color: var(--text-secondary); margin-bottom: 12px; line-height: 1.6; }

.profile-meta {
  display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;
}

.meta-chip {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 0.82rem; color: var(--text-muted);
}

.meta-chip .material-icons-round { font-size: 16px; }

.profile-skills { display: flex; flex-wrap: wrap; gap: 6px; }

.edit-btn { position: absolute; top: 24px; right: 24px; }

/* Tabs */
.tabs {
  display: flex; gap: 4px; margin-bottom: 2rem;
  border-bottom: 1px solid var(--border); padding-bottom: 0;
}

.tab {
  display: flex; align-items: center; gap: 6px;
  padding: 12px 18px; border: none; background: none;
  color: var(--text-muted); font-family: var(--font-body);
  font-size: 0.9rem; font-weight: 500; cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s var(--ease);
  margin-bottom: -1px;
}

.tab .material-icons-round { font-size: 18px; }
.tab:hover { color: var(--text-primary); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }

.tab-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem;
}

/* Portfolio */
.portfolio-item h4 { margin-bottom: 6px; }
.portfolio-item p { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 8px; }
.portfolio-link {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 0.85rem; margin-bottom: 8px;
}
.portfolio-link .material-icons-round { font-size: 16px; }

/* Reviews */
.reviews-list { display: flex; flex-direction: column; gap: 12px; }
.review-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.review-stars { display: flex; gap: 2px; }
.review-stars .material-icons-round { font-size: 18px; color: var(--text-muted); }
.review-stars .material-icons-round.filled { color: var(--accent); }
.review-date { font-size: 0.78rem; color: var(--text-muted); font-family: var(--font-mono); }
.review-item p { color: var(--text-secondary); font-size: 0.9rem; }

@media (max-width: 768px) {
  .profile-header { flex-direction: column; }
  .edit-btn { position: static; align-self: flex-start; }
}
</style>
