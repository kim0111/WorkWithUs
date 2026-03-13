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
        <span class="material-icons-round">edit</span>Edit
      </button>
    </div>

    <div class="tabs">
      <button v-for="t in tabs" :key="t" class="tab" :class="{ active: activeTab === t }" @click="activeTab = t">{{ t }}</button>
    </div>

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

    <section v-if="activeTab === 'Reviews'" class="tab-content">
      <div v-if="reviews.length" class="reviews-list">
        <div v-for="r in reviews" :key="r.id" class="review-card card">
          <div class="review-header">
            <div class="stars">{{ '\u2605'.repeat(Math.round(r.rating)) }}{{ '\u2606'.repeat(5 - Math.round(r.rating)) }}</div>
            <span class="text-muted">{{ fmtDate(r.created_at) }}</span>
          </div>
          <p v-if="r.comment" class="text-secondary">{{ r.comment }}</p>
          <span class="review-type badge badge-info">{{ r.review_type }}</span>
        </div>
      </div>
      <div v-else class="empty-state"><span class="material-icons-round">star_outline</span><h3>No reviews yet</h3></div>
    </section>

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

const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()
const user = ref(null)
const portfolio = ref([])
const reviews = ref([])
const rating = ref(null)
const activeTab = ref('Portfolio')
const showEdit = ref(false)
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
.page { padding: 2rem 24px; }
.profile-header { display: flex; gap: 20px; align-items: flex-start; padding-bottom: 1.5rem; border-bottom: 1px solid var(--gray-200); margin-bottom: 1.5rem; }
.profile-avatar {
  width: 64px; height: 64px; border-radius: 50%; background: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; font-weight: 600; color: white; flex-shrink: 0;
}
.profile-info { flex: 1; }
.profile-username { color: var(--gray-400); font-size: .8125rem; margin-top: 1px; }
.profile-meta { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 8px; font-size: .8125rem; color: var(--gray-400); }
.profile-meta > span { display: flex; align-items: center; gap: 4px; }
.profile-meta .material-icons-round { font-size: 14px; }
.profile-bio { margin-top: 10px; color: var(--gray-600); line-height: 1.6; font-size: .875rem; }
.profile-skills { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 10px; }
.tabs { display: flex; gap: 0; margin-bottom: 1.5rem; border-bottom: 1px solid var(--gray-200); }
.tab {
  padding: 8px 16px; border: none; background: none; color: var(--gray-500);
  font-family: var(--font); font-size: .8125rem; font-weight: 500; cursor: pointer;
  border-bottom: 2px solid transparent; transition: all .15s ease;
}
.tab.active { color: var(--accent-text); border-bottom-color: var(--accent); }
.tab:hover { color: var(--gray-700); }
.portfolio-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-bottom: 1.5rem; }
.portfolio-card { position: relative; }
.portfolio-card h4 { margin-bottom: 4px; font-size: .875rem; }
.portfolio-link { display: inline-flex; align-items: center; gap: 4px; font-size: .8125rem; margin-top: 6px; }
.portfolio-link .material-icons-round { font-size: 14px; }
.del-btn { position: absolute; top: 10px; right: 10px; }
.add-portfolio { padding-top: .75rem; border-top: 1px solid var(--gray-200); }
.add-portfolio h3 { margin-bottom: 10px; font-size: .9375rem; }
.pf-form { display: flex; flex-direction: column; gap: 8px; max-width: 440px; }
.reviews-list { display: flex; flex-direction: column; gap: 10px; }
.review-card { padding: 16px; }
.review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.stars { color: var(--warning); font-size: 1.1rem; letter-spacing: 1px; }
.review-type { margin-top: 6px; }
.modal-form { display: flex; flex-direction: column; gap: 14px; }
.text-muted { color: var(--gray-400); font-size: .8125rem; }
.text-secondary { color: var(--gray-600); font-size: .8125rem; line-height: 1.5; }
.loading-center { display: flex; justify-content: center; padding: 6rem; }
@media (max-width: 768px) { .profile-header { flex-direction: column; align-items: center; text-align: center; } .profile-meta { justify-content: center; } }
</style>
