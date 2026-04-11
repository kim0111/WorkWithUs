<template>
  <BaseModal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)" :title="title">
    <p class="confirm-message">{{ message }}</p>
    <template #footer>
      <button class="btn btn-secondary btn-sm" @click="$emit('update:modelValue', false)">Cancel</button>
      <button class="btn btn-sm" :class="confirmClass" @click="$emit('update:modelValue', false); $emit('confirm')">{{ confirmText }}</button>
    </template>
  </BaseModal>
</template>

<script setup>
import { computed } from 'vue'
import BaseModal from '@/components/BaseModal.vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  title: { type: String, default: 'Are you sure?' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: 'Delete' },
  variant: { type: String, default: 'danger' },
})

defineEmits(['update:modelValue', 'confirm'])

const confirmClass = computed(() =>
  props.variant === 'warning' ? 'btn-warning' : 'btn-danger'
)
</script>

<style scoped>
.confirm-message {
  color: var(--gray-600);
  font-size: 0.875rem;
  line-height: 1.6;
}
</style>
