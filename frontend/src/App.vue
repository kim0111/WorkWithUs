<template>
  <div class="app">
    <AppNavbar v-if="showNav" />
    <main class="main-content" :class="{ 'with-navbar': showNav }">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <ToastContainer />
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNavbar from '@/components/AppNavbar.vue'
import ToastContainer from '@/components/ToastContainer.vue'
const route = useRoute()
const showNav = computed(() => !['Login','Register','Home'].includes(route.name))
</script>
<style scoped>
.app{min-height:100vh}
.main-content.with-navbar{padding-top:72px}
</style>
