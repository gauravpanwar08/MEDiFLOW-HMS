import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({ baseURL: BASE_URL, headers: { 'Content-Type': 'application/json' } })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refresh = localStorage.getItem('refresh_token')
        if (!refresh) throw new Error('no token')
        const { data } = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh })
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (email, password, hospitalSlug = 'default') =>
    api.post('/auth/login', { email, password, hospital_slug: hospitalSlug }),
  me: () => api.get('/auth/me'),
  updateMe: (data) => api.patch('/auth/me', data),
  logout: () => api.post('/auth/logout'),
}

export const doctorApi = {
  list: (params) => api.get('/doctors', { params }),
  get: (id) => api.get(`/doctors/${id}`),
  update: (id, data) => api.patch(`/doctors/${id}`, data),
  availableSlots: (doctorId, date) => api.get(`/doctors/${doctorId}/slots`, { params: { date } }),
  getAvailability: (doctorId) => api.get(`/doctors/${doctorId}/availability`),
  setAvailability: (doctorId, data) => api.post(`/doctors/${doctorId}/availability`, data),
}

export const patientApi = {
  list: (params) => api.get('/patients', { params }),
  get: (id) => api.get(`/patients/${id}`),
  myProfile: () => api.get('/patients/me'),
  createProfile: (data) => api.post('/patients/me', data),
  update: (id, data) => api.patch(`/patients/${id}`, data),
}

export const appointmentApi = {
  list: (params) => api.get('/appointments', { params }),
  get: (id) => api.get(`/appointments/${id}`),
  create: (data) => api.post('/appointments', data),
  update: (id, data) => api.patch(`/appointments/${id}`, data),
}

export const recordApi = {
  list: (patientId, params) => api.get(`/records/patients/${patientId}`, { params }),
  upload: (patientId, file, meta = {}) => {
    const form = new FormData()
    form.append('file', file)
    if (meta.title) form.append('title', meta.title)
    if (meta.description) form.append('description', meta.description)
    if (meta.record_type) form.append('record_type', meta.record_type)
    return api.post(`/records/patients/${patientId}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  download: async (recordId) => {
    const res = await api.get(`/records/${recordId}/download`, { responseType: 'blob' })
    return res.data
  },
  delete: (recordId) => api.delete(`/records/${recordId}`),
}

export const analyticsApi = {
  summary: () => api.get('/analytics/summary'),
  workloads: () => api.get('/analytics/doctor-workload'),
  trends: (days = 30) => api.get('/analytics/trends', { params: { days } }),
}

export const aiApi = {
  analyzeSymptoms: (data) => api.post('/ai/symptom-analysis', data),
  chat: (message, conversationId) => api.post('/ai/chat', { message, conversation_id: conversationId }),
}

export const notificationApi = {
  list: () => api.get('/notifications'),
  markRead: (id) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
}

export const auditApi = {
  list: (params) => api.get('/audit', { params }),
}

export default api
