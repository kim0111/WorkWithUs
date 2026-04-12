<template>
  <div class="empty-state-wrapper">
    <span class="material-icons-round empty-icon">{{ icon }}</span>
    <h3>{{ title }}</h3>
    <p v-if="subtitle">{{ subtitle }}</p>
    <router-link v-if="actionText && actionTo" :to="actionTo" class="btn btn-primary btn-sm">{{ actionText }}</router-link>
    <button v-else-if="actionText" class="btn btn-primary btn-sm" @click="$emit('action')">{{ actionText }}</button>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, required: true },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  actionText: { type: String, default: '' },
  actionTo: { type: String, default: '' },
})

defineEmits(['action'])
</script>

<style scoped>
.empty-state-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 8px;
  text-align: center;
}
.empty-icon {
  font-size: 48px;
  color: var(--gray-300);
}
.empty-state-wrapper h3 {
  color: var(--gray-600);
  font-weight: 500;
}
.empty-state-wrapper p {
  color: var(--gray-400);
  font-size: 0.875rem;
}
</style>
