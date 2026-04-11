<template>
  <div class="form-field" :class="{ 'has-error': error }">
    <label class="field-label">{{ label }}</label>
    <slot />
    <div class="field-footer">
      <span v-if="error" class="field-error">{{ error }}</span>
      <span v-else-if="hint" class="field-hint">{{ hint }}</span>
      <span v-if="maxLength" class="char-count">{{ currentLength }}/{{ maxLength }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  maxLength: { type: Number, default: 0 },
})

const currentLength = ref(0)
</script>

<style scoped>
.form-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.field-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--gray-700);
}
.field-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 18px;
}
.field-error {
  color: var(--danger);
  font-size: 0.75rem;
}
.field-hint {
  color: var(--gray-400);
  font-size: 0.75rem;
}
.char-count {
  color: var(--gray-400);
  font-size: 0.75rem;
  margin-left: auto;
}
.has-error :slotted(input),
.has-error :slotted(textarea),
.has-error :slotted(select) {
  border-color: var(--danger);
}
</style>
