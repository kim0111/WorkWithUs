<template>
  <div class="info-grid">
    <div class="info-item">
      <div class="info-label">University</div>
      <div class="info-value">{{ profile?.university || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Major</div>
      <div class="info-value">{{ profile?.major || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Graduation</div>
      <div class="info-value">{{ profile?.graduation_year || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Completed</div>
      <div class="info-value">{{ profile?.completed_projects_count || 0 }} projects</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  profile: { type: Object, default: null },
})
</script>

<style scoped>
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--gray-200);
}
.info-label {
  font-size: 0.6875rem;
  text-transform: uppercase;
  color: var(--gray-400);
  letter-spacing: 0.5px;
  font-weight: 500;
}
.info-value {
  font-size: 0.875rem;
  margin-top: 4px;
  color: var(--gray-900);
}
@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
