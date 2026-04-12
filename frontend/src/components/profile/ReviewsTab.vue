<template>
  <div>
    <div v-if="reviews.length" class="reviews-list">
      <div v-for="r in reviews" :key="r.id" class="review-card card">
        <div class="review-header">
          <div class="stars">{{ '\u2605'.repeat(Math.round(r.rating)) }}{{ '\u2606'.repeat(5 - Math.round(r.rating)) }}</div>
          <span class="text-muted">{{ fmtDate(r.created_at) }}</span>
        </div>
        <p v-if="r.comment" class="review-comment">{{ r.comment }}</p>
        <span class="badge badge-info review-type">{{ r.review_type }}</span>
      </div>
    </div>
    <EmptyState v-else icon="star_outline" title="No reviews yet" subtitle="Reviews will appear here after project collaborations" />
  </div>
</template>

<script setup>
import EmptyState from '@/components/EmptyState.vue'

defineProps({
  reviews: { type: Array, default: () => [] },
})

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}
</script>

<style scoped>
.reviews-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.review-card {
  padding: 16px;
}
.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.stars {
  color: var(--warning);
  font-size: 1.1rem;
  letter-spacing: 1px;
}
.review-comment {
  color: var(--gray-600);
  font-size: 0.8125rem;
  line-height: 1.5;
}
.review-type {
  margin-top: 6px;
}
.text-muted {
  color: var(--gray-400);
  font-size: 0.8125rem;
}
</style>
