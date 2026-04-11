<template>
  <div class="not-found">
    <h1 class="not-found-code">404</h1>
    <p class="not-found-message">This page doesn't exist</p>
    <router-link to="/" class="btn btn-primary">Back to home</router-link>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 12px;
  text-align: center;
  padding: 24px;
}
.not-found-code {
  font-size: 4rem;
  font-weight: 700;
  color: var(--gray-300);
  line-height: 1;
}
.not-found-message {
  color: var(--gray-500);
  font-size: 1rem;
}
</style>
