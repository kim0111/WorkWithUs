<template>
  <div v-if="totalPages > 1" class="pagination">
    <button class="btn btn-ghost btn-sm" :disabled="currentPage <= 1" @click="go(currentPage - 1)">
      <span class="material-icons-round">chevron_left</span>
    </button>
    <template v-for="p in pages" :key="p">
      <span v-if="p === '...'" class="pagination-ellipsis">...</span>
      <button
        v-else
        class="btn btn-sm pagination-page"
        :class="{ 'pagination-active': p === currentPage }"
        @click="go(p)"
      >{{ p }}</button>
    </template>
    <button class="btn btn-ghost btn-sm" :disabled="currentPage >= totalPages" @click="go(currentPage + 1)">
      <span class="material-icons-round">chevron_right</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
})

const emit = defineEmits(['update:currentPage'])

function go(page) {
  if (page >= 1 && page <= props.totalPages) {
    emit('update:currentPage', page)
  }
}

const pages = computed(() => {
  const total = props.totalPages
  const current = props.currentPage
  if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1)

  const result = []
  result.push(1)
  if (current > 3) result.push('...')
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
    result.push(i)
  }
  if (current < total - 2) result.push('...')
  result.push(total)
  return result
})
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 1.5rem;
}
.pagination-ellipsis {
  padding: 4px 6px;
  color: var(--gray-400);
  font-size: 0.8125rem;
}
.pagination-page {
  background: none;
  color: var(--gray-600);
  border: 1px solid transparent;
  min-width: 32px;
  justify-content: center;
}
.pagination-page:hover {
  background: var(--gray-100);
}
.pagination-active {
  background: var(--accent) !important;
  color: #fff !important;
  border-color: var(--accent);
}
</style>
