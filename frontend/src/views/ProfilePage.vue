<template>
  <div v-if="user" class="page container">
    <div class="profile-header">
      <div class="profile-avatar">{{ (user.full_name || user.username)[0].toUpperCase() }}</div>
      <div class="profile-info">
        <h1>{{ user.full_name || user.username }}</h1>
        <p class="profile-username">@{{ user.username }}</p>
        <div class="profile-meta">
          <span class="badge" :class="roleBadge">{{ user.role }}</span>
          <span><span class="material-icons-round">email</span>{{ user.email }}</span>
          <span><span class="material-icons-round">calendar_today</span>Joined {{ fmtDate(user.created_at) }}</span>
          <span v-if="rating"><span class="material-icons-round">star</span>{{ rating.average_rating }}/5 ({{ rating.total_reviews }} reviews)</span>
        </div>
        <p v-if="user.bio" class="profile-bio">{{ user.bio }}</p>
        <div v-if="user.skills?.length" class="profile-skills">
          <span v-for="s in user.skills" :key="s.id" class="skill-tag">{{ s.name }}</span>
        </div>
      </div>
      <button v-if="isMe" class="btn btn-secondary btn-sm" @click="showEdit = true">
        <span class="material-icons-round">edit</span>Edit Profile
      </button>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button v-for="t in tabs" :key="t" class="tab" :class="{ active: activeTab === t }" @click="activeTab = t">{{ t }}</button>
    </div>

    <!-- Portfolio -->
    <section v-if="activeTab === 'Portfolio'" class="tab-content">
      <div v-if="portfolio.length" class="portfolio-grid">
        <div v-for="p in portfolio" :key="p.id" class="portfolio-card card">
          <h4>{{ p.title }}</h4>
          <p v-if="p.description" class="text-secondary">{{ p.description }}</p>
          <a v-if="p.project_url" :href="p.project_url" target="_blank" class="portfolio-link">
            <span class="material-icons-round">open_in_new</span>View
          </a>
          <button v-if="isMe" class="btn btn-ghost btn-sm del-btn" @click="delPortfolio(p.id)">
            <span class="material-icons-round">delete</span>
          </button>
        </div>
      </div>
      <div v-else class="empty-state"><span class="material-icons-round">collections</span><h3>No portfolio items</h3></div>
      <div v-if="isMe" class="add-portfolio">
        <h3>Add Portfolio Item</h3>
        <form @submit.prevent="addPortfolio" class="pf-form">
          <input class="input" v-model="pf.title" placeholder="Title" required />
          <input class="input" v-model="pf.description" placeholder="Description" />
          <input class="input" v-model="pf.project_url" placeholder="URL (optional)" />
          <button type="submit" class="btn btn-primary btn-sm">Add</button>
        </form>
      </div>
    </section>

    <!-- Reviews -->
    <section v-if="activeTab === 'Reviews'" class="tab-content">
      <div v-if="reviews.length" class="reviews-list">
        <div v-for="r in reviews" :key="r.id" class="review-card card">
          <div class="review-header">
            <div class="stars">{{ '★'.repeat(Math.round(r.rating)) }}{{ '☆'.repeat(5 - Math.round(r.rating)) }}</div>
            <span class="text-muted">{{ fmtDate(r.created_at) }}</span>
          </div>
          <p v-if="r.comment" class="text-secondary">{{ r.comment }}</p>
          <span class="review-type badge badge-info">{{ r.review_type }}</span>
        </div>
      </div>
      <div v-else class="empty-state"><span class="material-icons-round">rate_review</span><h3>No reviews yet</h3></div>
    </section>

    <!-- Edit Modal -->
    <div v-if="showEdit" class="modal-overlay" @click.self="showEdit = false">
      <div class="modal">
        <div class="modal-header"><h3>Edit Profile</h3><button class="btn btn-ghost btn-sm" @click="showEdit = false"><span class="material-icons-round">close</span></button></div>
        <form @submit.prevent="saveProfile" class="modal-form">
          <div class="input-group"><label>Full Name</label><input class="input" v-model="editForm.full_name" /></div>
          <div class="input-group"><label>Bio</label><textarea class="input" v-model="editForm.bio" rows="4"></textarea></div>
          <button type="submit" class="btn btn-primary">Save Changes</button>
        </form>
      </div>
    </div>
  </div>
  <div v-else class="loading-center"><div class="spinner"></div></div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { usersAPI, portfolioAPI, reviewsAPI } from '@/api'

const route = useRoute(); const auth = useAuthStore(); const toast = useToastStore()
const user = ref(null); const portfolio = ref([]); const reviews = ref([]); const rating = ref(null)
const activeTab = ref('Portfolio'); const showEdit = ref(false)
const tabs = ['Portfolio', 'Reviews']
const pf = reactive({ title: '', description: '', project_url: '' })
const editForm = reactive({ full_name: '', bio: '' })
const isMe = computed(() => auth.user?.id === Number(route.params.id))
const roleBadge = computed(() => ({ student: 'badge-teal', company: 'badge-accent', admin: 'badge-danger', committee: 'badge-info' }[user.value?.role]))
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '' }

async function load() {
  const id = route.params.id
  try { user.value = (await usersAPI.get(id)).data; editForm.full_name = user.value.full_name || ''; editForm.bio = user.value.bio || '' } catch {}
  try { portfolio.value = (await portfolioAPI.byUser(id)).data } catch {}
  try { reviews.value = (await reviewsAPI.forUser(id)).data } catch {}
  try { rating.value = (await reviewsAPI.rating(id)).data } catch {}
}
async function addPortfolio() {
  try { await portfolioAPI.add(pf); toast.success('Added!'); pf.title = ''; pf.description = ''; pf.project_url = ''; await load() } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}
async function delPortfolio(id) { try { await portfolioAPI.delete(id); toast.success('Deleted'); await load() } catch {} }
async function saveProfile() {
  try { await usersAPI.update(user.value.id, editForm); toast.success('Profile updated'); showEdit.value = false; await load(); await auth.fetchUser() } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}
onMounted(load)
</script>

<style scoped>
.page { padding: 2rem; }
.profile-header { display: flex; gap: 24px; align-items: flex-start; padding-bottom: 2rem; border-bottom: 1px solid var(--border); margin-bottom: 2rem; }
.profile-avatar { width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), #d4822a); display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 700; color: var(--text-inverse); flex-shrink: 0; }
.profile-info { flex: 1; }
.profile-username { color: var(--text-muted); font-size: .9rem; margin-top: 2px; }
.profile-meta { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 10px; font-size: .85rem; color: var(--text-muted); }
.profile-meta > span { display: flex; align-items: center; gap: 5px; }
.profile-meta .material-icons-round { font-size: 16px; }
.profile-bio { margin-top: 12px; color: var(--text-secondary); line-height: 1.6; }
.profile-skills { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.tabs { display: flex; gap: 4px; margin-bottom: 2rem; border-bottom: 1px solid var(--border); }
.tab { padding: 10px 20px; border: none; background: none; color: var(--text-secondary); font-family: var(--font-body); font-size: .9rem; font-weight: 500; cursor: pointer; border-bottom: 2px solid transparent; transition: all .2s; }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.portfolio-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-bottom: 2rem; }
.portfolio-card { position: relative; padding: 20px; }
.portfolio-card h4 { margin-bottom: 6px; }
.portfolio-link { display: inline-flex; align-items: center; gap: 4px; color: var(--accent); font-size: .85rem; margin-top: 8px; }
.del-btn { position: absolute; top: 12px; right: 12px; }
.add-portfolio { padding-top: 1rem; border-top: 1px solid var(--border); }
.add-portfolio h3 { margin-bottom: 12px; font-size: 1.1rem; }
.pf-form { display: flex; flex-direction: column; gap: 10px; max-width: 500px; }
.reviews-list { display: flex; flex-direction: column; gap: 14px; }
.review-card { padding: 20px; }
.review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.stars { color: var(--accent); font-size: 1.3rem; letter-spacing: 2px; }
.review-type { margin-top: 8px; }
.modal-form { display: flex; flex-direction: column; gap: 16px; }
.text-muted { color: var(--text-muted); font-size: .9rem; }
.text-secondary { color: var(--text-secondary); font-size: .9rem; line-height: 1.5; }
.loading-center { display: flex; justify-content: center; padding: 6rem; }
@media (max-width: 768px) { .profile-header { flex-direction: column; align-items: center; text-align: center; } .profile-meta { justify-content: center; } }
</style>
