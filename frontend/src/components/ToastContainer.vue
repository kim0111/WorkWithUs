<template>
  <div class="toast-container">
    <transition-group name="fade">
      <div v-for="t in ts.toasts" :key="t.id" class="toast" :class="`toast-${t.type}`" @click="ts.toasts = ts.toasts.filter(x=>x.id!==t.id)">
        <span class="material-icons-round">{{ t.type === 'success' ? 'check_circle' : 'error' }}</span>
        {{ t.message }}
      </div>
    </transition-group>
  </div>
</template>
<script setup>
import { useToastStore } from '@/stores/toast'
const ts = useToastStore()
</script>
