import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomePage.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/LoginPage.vue'), meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterPage.vue'), meta: { guest: true } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/DashboardPage.vue'), meta: { auth: true } },
  { path: '/projects', name: 'Projects', component: () => import('@/views/ProjectsPage.vue') },
  { path: '/projects/create', name: 'CreateProject', component: () => import('@/views/CreateProjectPage.vue'), meta: { auth: true } },
  { path: '/projects/:id', name: 'ProjectDetail', component: () => import('@/views/ProjectDetailPage.vue') },
  { path: '/profile/:id', name: 'Profile', component: () => import('@/views/ProfilePage.vue') },
  { path: '/my-applications', name: 'MyApps', component: () => import('@/views/MyApplicationsPage.vue'), meta: { auth: true } },
  { path: '/chat', name: 'ChatList', component: () => import('@/views/ChatListPage.vue'), meta: { auth: true } },
  { path: '/chat/:roomId', name: 'ChatRoom', component: () => import('@/views/ChatRoomPage.vue'), meta: { auth: true } },
  { path: '/notifications', name: 'Notifications', component: () => import('@/views/NotificationsPage.vue'), meta: { auth: true } },
  { path: '/admin', name: 'Admin', component: () => import('@/views/AdminPage.vue'), meta: { auth: true, admin: true } },
]

const router = createRouter({ history: createWebHistory(), routes, scrollBehavior: () => ({ top: 0 }) })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.user && localStorage.getItem('access_token')) await auth.fetchUser()
  if (to.meta.auth && !auth.isAuth) return '/login'
  if (to.meta.guest && auth.isAuth) return '/dashboard'
  if (to.meta.admin && !auth.isAdmin) return '/dashboard'
})

export default router
