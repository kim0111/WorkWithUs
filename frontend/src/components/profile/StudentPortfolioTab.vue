<template>
  <div>
    <div v-if="portfolio.length" class="portfolio-grid">
      <div v-for="p in portfolio" :key="p.id" class="portfolio-card">
        <div class="portfolio-image">
          <span class="material-icons-round">code</span>
        </div>
        <div class="portfolio-body">
          <h4>{{ p.title }}</h4>
          <p v-if="p.description" class="portfolio-desc">{{ p.description }}</p>
          <div class="portfolio-footer">
            <a v-if="p.project_url" :href="p.project_url" target="_blank" class="portfolio-link">
              View project <span class="material-icons-round">open_in_new</span>
            </a>
            <button v-if="isOwner" class="btn btn-ghost btn-sm del-btn" @click="confirmDelete(p.id)">
              <span class="material-icons-round">delete</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    <EmptyState v-else icon="collections" title="No portfolio items" subtitle="Showcase your work by adding portfolio items" />

    <div v-if="isOwner" class="add-portfolio">
      <h3>Add Portfolio Item</h3>
      <form @submit.prevent="addItem" class="pf-form">
        <input class="input" v-model="form.title" placeholder="Title" required />
        <input class="input" v-model="form.description" placeholder="Description" />
        <input class="input" v-model="form.project_url" placeholder="URL (optional)" />
        <button type="submit" class="btn btn-primary btn-sm">Add</button>
      </form>
    </div>

    <ConfirmDialog
      v-model="showConfirm"
      title="Delete Portfolio Item"
      message="This portfolio item will be permanently removed."
      @confirm="doDelete"
    />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { portfolioAPI } from '@/api'
import { useToastStore } from '@/stores/toast'
import EmptyState from '@/components/EmptyState.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const props = defineProps({
  portfolio: { type: Array, default: () => [] },
  isOwner: { type: Boolean, default: false },
})

const emit = defineEmits(['updated'])

const toast = useToastStore()
const form = reactive({ title: '', description: '', project_url: '' })
const showConfirm = ref(false)
const deleteId = ref(null)

function confirmDelete(id) {
  deleteId.value = id
  showConfirm.value = true
}

async function doDelete() {
  showConfirm.value = false
  try {
    await portfolioAPI.delete(deleteId.value)
    toast.success('Portfolio item deleted')
    emit('updated')
  } catch {
    toast.error('Failed to delete')
  }
}

async function addItem() {
  try {
    await portfolioAPI.add(form)
    toast.success('Added!')
    form.title = ''
    form.description = ''
    form.project_url = ''
    emit('updated')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed')
  }
}
</script>

<style scoped>
.portfolio-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 1.5rem;
}
.portfolio-card {
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  overflow: hidden;
  background: var(--white);
}
.portfolio-image {
  height: 120px;
  background: var(--gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
}
.portfolio-image .material-icons-round {
  font-size: 32px;
  color: var(--gray-300);
}
.portfolio-body {
  padding: 14px 16px;
}
.portfolio-body h4 {
  font-size: 0.875rem;
  margin-bottom: 4px;
}
.portfolio-desc {
  color: var(--gray-500);
  font-size: 0.8125rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.portfolio-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.portfolio-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8125rem;
  color: var(--accent-text);
}
.portfolio-link .material-icons-round {
  font-size: 14px;
}
.del-btn {
  color: var(--gray-400);
}
.del-btn:hover {
  color: var(--danger);
}
.add-portfolio {
  padding-top: 0.75rem;
  border-top: 1px solid var(--gray-200);
}
.add-portfolio h3 {
  margin-bottom: 10px;
  font-size: 0.9375rem;
}
.pf-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 440px;
}
</style>
