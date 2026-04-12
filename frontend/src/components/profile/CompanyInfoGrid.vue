<template>
  <div class="info-grid">
    <div class="info-item">
      <div class="info-label">Industry</div>
      <div class="info-value">{{ profile?.industry || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Website</div>
      <div class="info-value">
        <a v-if="profile?.website" :href="websiteUrl" target="_blank" class="info-link">{{ profile.website }}</a>
        <span v-else>Not specified</span>
      </div>
    </div>
    <div class="info-item">
      <div class="info-label">Location</div>
      <div class="info-value">{{ profile?.location || 'Not specified' }}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Projects</div>
      <div class="info-value">{{ projectCount }} posted</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  profile: { type: Object, default: null },
  projectCount: { type: Number, default: 0 },
})

const websiteUrl = computed(() => {
  const url = props.profile?.website || ''
  return url.startsWith('http') ? url : `https://${url}`
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
.info-link {
  color: var(--accent-text);
  font-size: 0.875rem;
}
@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
