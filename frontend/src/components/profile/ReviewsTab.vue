<template>
  <div>
    <div v-if="reviews.length" class="reviews-list">
      <div v-for="r in reviews" :key="r.id" class="review-card card">
        <div class="review-header">
          <router-link :to="`/profile/${r.reviewer_id}`" class="reviewer">
            <div class="av-sm">{{ (reviewerName(r) || '?').charAt(0).toUpperCase() }}</div>
            <div class="reviewer-meta">
              <span class="reviewer-name">{{ reviewerName(r) }}</span>
              <span class="reviewer-role">{{ reviewerRoleLabel(r) }}</span>
            </div>
          </router-link>
          <div class="review-header-right">
            <div class="stars">{{ '\u2605'.repeat(Math.round(r.rating)) }}{{ '\u2606'.repeat(5 - Math.round(r.rating)) }}</div>
            <span class="text-muted">{{ fmtDate(r.created_at) }}</span>
          </div>
        </div>
        <p v-if="r.comment" class="review-comment">{{ r.comment }}</p>
        <div v-if="r.project_title" class="review-project">
          <span class="material-icons-round">folder_open</span>
          <router-link :to="`/projects/${r.project_id}`">{{ r.project_title }}</router-link>
        </div>
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

function reviewerName(r) {
  return r.reviewer_full_name || r.reviewer_username || `User #${r.reviewer_id}`
}

function reviewerRoleLabel(r) {
  const role = r.reviewer_role
  if (role === 'company') return 'Project owner'
  if (role === 'student') return 'Team member'
  if (role === 'admin') return 'Administrator'
  if (role === 'committee') return 'Committee'
  if (r.review_type === 'owner_to_student') return 'Project owner'
  if (r.review_type === 'student_to_owner') return 'Team member'
  return ''
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
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
}
.reviewer {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
  min-width: 0;
}
.av-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.8125rem;
  flex-shrink: 0;
}
.reviewer-meta { display: flex; flex-direction: column; min-width: 0; }
.reviewer-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--gray-900);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.reviewer-role {
  font-size: 0.6875rem;
  color: var(--gray-500);
}
.review-header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
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
  margin-bottom: 8px;
}
.review-project {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: var(--gray-500);
}
.review-project a {
  color: var(--accent);
  text-decoration: none;
}
.review-project a:hover { text-decoration: underline; }
.review-project .material-icons-round { font-size: 14px; }
.text-muted {
  color: var(--gray-400);
  font-size: 0.75rem;
}
</style>
