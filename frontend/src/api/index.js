import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

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
  register: d => api.post('/auth/register', d),
  login: d => api.post('/auth/login', d),
  me: () => api.get('/auth/me'),
  refresh: t => api.post('/auth/refresh', { refresh_token: t }),
  logout: () => api.post('/auth/logout'),
}

// ── Users ───────────────────────────────────────────
export const usersAPI = {
  get: id => api.get(`/users/${id}`),
  update: (id, d) => api.put(`/users/${id}`, d),
  addSkill: (uid, sid) => api.post(`/users/${uid}/skills/${sid}`),
  removeSkill: (uid, sid) => api.delete(`/users/${uid}/skills/${sid}`),
}

// ── Skills ──────────────────────────────────────────
export const skillsAPI = {
  list: () => api.get('/skills/'),
  create: d => api.post('/skills/', d),
}

// ── Projects ────────────────────────────────────────
export const projectsAPI = {
  list: p => api.get('/projects/', { params: p }),
  get: id => api.get(`/projects/${id}`),
  create: d => api.post('/projects/', d),
  update: (id, d) => api.put(`/projects/${id}`, d),
  delete: id => api.delete(`/projects/${id}`),
}

// ── Applications ────────────────────────────────────
export const applicationsAPI = {
  apply: d => api.post('/applications/', d),
  updateStatus: (id, d) => api.put(`/applications/${id}/status`, d),
  byProject: pid => api.get(`/applications/project/${pid}`),
  my: () => api.get('/applications/my'),
}

// ── Files ───────────────────────────────────────────
export const filesAPI = {
  upload: (projectId, file, fileType = 'attachment') => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`/files/project/${projectId}?file_type=${fileType}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  list: (projectId, fileType) => api.get(`/files/project/${projectId}`, { params: fileType ? { file_type: fileType } : {} }),
  download: id => api.get(`/files/${id}/download`),
  delete: id => api.delete(`/files/${id}`),
}

// ── Chat ────────────────────────────────────────────
export const chatAPI = {
  createRoom: (projectId, userId) => api.post(`/chat/rooms/${projectId}/${userId}`),
  myRooms: () => api.get('/chat/rooms'),
  messages: (roomId, page = 1) => api.get(`/chat/rooms/${roomId}/messages`, { params: { page } }),
  send: (roomId, content) => api.post(`/chat/rooms/${roomId}/messages`, { content }),
  connectWs: (roomId) => {
    const token = localStorage.getItem('access_token')
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.hostname
    return new WebSocket(`${proto}://${host}:8000/api/v1/chat/ws/${roomId}?token=${token}`)
  },
}

// ── Notifications ───────────────────────────────────
export const notificationsAPI = {
  list: (unread, page = 1) => api.get('/notifications/', { params: { unread_only: unread || false, page } }),
  unreadCount: () => api.get('/notifications/unread-count'),
  markRead: id => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
}

// ── Reviews ─────────────────────────────────────────
export const reviewsAPI = {
  create: d => api.post('/reviews/', d),
  forUser: uid => api.get(`/reviews/user/${uid}`),
  rating: uid => api.get(`/reviews/user/${uid}/rating`),
}

// ── Portfolio ───────────────────────────────────────
export const portfolioAPI = {
  byUser: uid => api.get(`/portfolio/user/${uid}`),
  add: d => api.post('/portfolio/', d),
  delete: id => api.delete(`/portfolio/${id}`),
}

// ── Admin ───────────────────────────────────────────
export const adminAPI = {
  stats: () => api.get('/admin/stats'),
  users: p => api.get('/admin/users', { params: p }),
  updateUser: (id, d) => api.put(`/admin/users/${id}`, d),
}
