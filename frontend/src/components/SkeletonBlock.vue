<template>
  <div
    class="skeleton-block"
    :style="{ width, height, borderRadius }"
  />
</template>

<script setup>
defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: '16px' },
  borderRadius: { type: String, default: 'var(--radius-md)' },
})
</script>

<style scoped>
.skeleton-block {
  background: var(--gray-200);
  background-image: linear-gradient(
    90deg,
    var(--gray-200) 0%,
    var(--gray-100) 40%,
    var(--gray-200) 80%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
