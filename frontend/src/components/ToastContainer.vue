<template>
  <div class="toast-container">
    <transition-group name="fade">
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        class="toast"
        :class="`toast-${toast.type}`"
        @click="toastStore.remove(toast.id)"
      >
        <span class="material-icons-round">
          {{ toast.type === 'success' ? 'check_circle' : 'error' }}
        </span>
        {{ toast.message }}
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useToastStore } from '@/stores/toast'
const toastStore = useToastStore()
</script>
