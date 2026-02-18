import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

// Request interceptor — attach JWT
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — handle 401 with refresh
api.interceptors.response.use(
  res => res,
  async error => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api

// ── Auth ────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  refresh: (token) => api.post('/auth/refresh', { refresh_token: token }),
}

// ── Users ───────────────────────────────────────────
export const usersAPI = {
  get: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.put(`/users/${id}`, data),
  addSkill: (userId, skillId) => api.post(`/users/${userId}/skills/${skillId}`),
  removeSkill: (userId, skillId) => api.delete(`/users/${userId}/skills/${skillId}`),
}

// ── Projects ────────────────────────────────────────
export const projectsAPI = {
  list: (params) => api.get('/projects/', { params }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects/', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
}

// ── Applications ────────────────────────────────────
export const applicationsAPI = {
  apply: (data) => api.post('/applications/', data),
  updateStatus: (id, data) => api.put(`/applications/${id}/status`, data),
  byProject: (projectId) => api.get(`/applications/project/${projectId}`),
  my: () => api.get('/applications/my'),
}

// ── Portfolio ───────────────────────────────────────
export const portfolioAPI = {
  getByUser: (userId) => api.get(`/portfolio/user/${userId}`),
  add: (data) => api.post('/portfolio/', data),
  delete: (id) => api.delete(`/portfolio/${id}`),
}

// ── Reviews ─────────────────────────────────────────
export const reviewsAPI = {
  getForUser: (userId) => api.get(`/reviews/user/${userId}`),
  getRating: (userId) => api.get(`/reviews/user/${userId}/rating`),
  create: (data) => api.post('/reviews/', data),
}

// ── Skills ──────────────────────────────────────────
export const skillsAPI = {
  list: () => api.get('/skills/'),
  create: (data) => api.post('/skills/', data),
}

// ── Notifications ───────────────────────────────────
export const notificationsAPI = {
  list: (unread) => api.get('/notifications/', { params: { unread_only: unread || false } }),
  markRead: (id) => api.put(`/notifications/${id}/read`),
}

// ── Admin ───────────────────────────────────────────
export const adminAPI = {
  stats: () => api.get('/admin/stats'),
  users: (params) => api.get('/admin/users', { params }),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
}
