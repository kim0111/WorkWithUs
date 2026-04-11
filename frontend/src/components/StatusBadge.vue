<template>
  <span class="status-badge" :class="[colorClass, sizeClass]">{{ formatted }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  size: { type: String, default: 'sm' },
})

const colorMap = {
  open: 'status-green',
  in_progress: 'status-amber',
  closed: 'status-red',
  rejected: 'status-red',
  revision_requested: 'status-red',
  pending: 'status-gray',
  accepted: 'status-green',
  approved: 'status-green',
  completed: 'status-green',
  submitted: 'status-purple',
}

const colorClass = computed(() => colorMap[props.status] || 'status-gray')
const sizeClass = computed(() => props.size === 'md' ? 'status-md' : 'status-sm')
const formatted = computed(() =>
  props.status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
)
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 16px;
  font-weight: 500;
  letter-spacing: 0.01em;
  white-space: nowrap;
}
.status-sm {
  padding: 2px 8px;
  font-size: 0.6875rem;
}
.status-md {
  padding: 3px 10px;
  font-size: 0.75rem;
}
.status-green {
  background: var(--success-light);
  color: var(--success);
}
.status-amber {
  background: var(--warning-light);
  color: var(--warning);
}
.status-red {
  background: var(--danger-light);
  color: var(--danger);
}
.status-gray {
  background: var(--gray-100);
  color: var(--gray-500);
}
.status-purple {
  background: #f3e8ff;
  color: #7c3aed;
}
[data-theme="dark"] .status-purple {
  background: #2e1065;
  color: #c4b5fd;
}
</style>
