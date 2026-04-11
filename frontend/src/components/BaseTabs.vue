<template>
  <div class="base-tabs">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="base-tab"
      :class="{ active: modelValue === tab.key }"
      @click="$emit('update:modelValue', tab.key)"
    >
      {{ tab.label }}<span v-if="tab.count != null" class="tab-count">({{ tab.count }})</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.base-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--gray-200);
  margin-bottom: 1.5rem;
}
.base-tab {
  padding: 10px 20px;
  border: none;
  background: none;
  color: var(--gray-500);
  font-family: var(--font);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s ease;
}
.base-tab.active {
  color: var(--accent-text);
  border-bottom-color: var(--accent);
  font-weight: 600;
}
.base-tab:hover {
  color: var(--gray-700);
}
.tab-count {
  margin-left: 4px;
  color: var(--gray-400);
  font-weight: 400;
}
.base-tab.active .tab-count {
  color: var(--accent-text);
}
</style>
