<template>
  <div class="dashboard container">
    <header class="dh"><div><p class="dg">Welcome back,</p><h1>{{ auth.user?.full_name || auth.user?.username }}</h1></div>
      <span class="badge" :class="rb">{{ auth.user?.role }}</span></header>
    <div v-if="stats" class="stats-row">
      <div class="stat-card" v-for="s in sc" :key="s.l"><div class="stat-label">{{s.l}}</div><div class="stat-value">{{s.v}}</div></div>
    </div>
    <section class="ds">
      <h2>Quick Actions</h2>
      <div class="ag">
        <router-link v-if="auth.isCompany||auth.isAdmin" to="/projects/create" class="ac"><span class="material-icons-round">add_circle</span><div><h4>New Project</h4><p>Publish a project</p></div></router-link>
        <router-link to="/projects" class="ac"><span class="material-icons-round">explore</span><div><h4>Browse Projects</h4><p>Discover opportunities</p></div></router-link>
        <router-link to="/chat" class="ac"><span class="material-icons-round">chat</span><div><h4>Messages</h4><p>Chat with collaborators</p></div></router-link>
        <router-link v-if="auth.isStudent" to="/my-applications" class="ac"><span class="material-icons-round">send</span><div><h4>My Applications</h4><p>Track submissions</p></div></router-link>
        <router-link :to="`/profile/${auth.user?.id}`" class="ac"><span class="material-icons-round">person</span><div><h4>Profile</h4><p>Edit profile & portfolio</p></div></router-link>
      </div>
    </section>
    <section class="ds">
      <div class="st"><h2>Recent Projects</h2><router-link to="/projects" class="btn btn-ghost btn-sm">View All<span class="material-icons-round">arrow_forward</span></router-link></div>
      <div v-if="projects.length" class="grid-2"><ProjectCard v-for="p in projects" :key="p.id" :project="p" /></div>
      <div v-else class="empty-state"><span class="material-icons-round">folder_open</span><h3>No projects yet</h3></div>
    </section>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { projectsAPI, adminAPI, applicationsAPI } from '@/api'
import ProjectCard from '@/components/ProjectCard.vue'
const auth=useAuthStore(); const projects=ref([]); const stats=ref(null); const myApps=ref(0)
const rb=computed(()=>({student:'badge-teal',company:'badge-accent',admin:'badge-danger',committee:'badge-info'}[auth.user?.role]||'badge-info'))
const sc=computed(()=>{
  if(auth.isAdmin&&stats.value) return [{l:'Users',v:stats.value.total_users},{l:'Projects',v:stats.value.total_projects},{l:'Applications',v:stats.value.total_applications},{l:'Chat Messages',v:stats.value.total_chat_messages}]
  return [{l:'Projects',v:projects.value.length},{l:'My Applications',v:myApps.value}]
})
onMounted(async()=>{
  try{projects.value=(await projectsAPI.list({page:1,size:4})).data.items}catch{}
  if(auth.isAdmin){try{stats.value=(await adminAPI.stats()).data}catch{}}
  if(auth.isStudent){try{myApps.value=(await applicationsAPI.my()).data.length}catch{}}
})
</script>
<style scoped>
.dashboard{padding:2rem}
.dh{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:2rem;padding-bottom:2rem;border-bottom:1px solid var(--border)}
.dg{font-size:.9rem;color:var(--text-muted);margin-bottom:4px}
.stats-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-bottom:2.5rem}
.ds{margin-bottom:3rem}.ds h2{margin-bottom:1.2rem}
.st{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.2rem}
.ag{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.ac{display:flex;align-items:center;gap:16px;padding:20px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);text-decoration:none;color:inherit;transition:all .25s var(--ease)}
.ac:hover{border-color:var(--accent);transform:translateY(-2px);box-shadow:var(--shadow-glow)}
.ac .material-icons-round{font-size:32px;color:var(--accent)}
.ac h4{font-family:var(--font-body);font-weight:600;margin-bottom:2px}.ac p{font-size:.82rem;color:var(--text-muted)}
</style>
