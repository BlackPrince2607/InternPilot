import axios from 'axios'
import { supabase } from './supabase'

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 25000
})

// 🔥 Attach token automatically (skip OPTIONS requests)
api.interceptors.request.use(async (config) => {
  // Skip preflight OPTIONS requests
  if (config.method === 'options') {
    return config
  }

  const { data, error } = await supabase.auth.getSession()
  if (error) {
    return Promise.reject(error)
  }

  const token = data.session?.access_token

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // For FormData, let axios set Content-Type automatically
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }

  return config
}, (error) => {
  return Promise.reject(error)
})

api.interceptors.response.use(
  (response) => {
    const payload = response.data

    if (payload && typeof payload === 'object' && Object.prototype.hasOwnProperty.call(payload, 'success')) {
      if (payload.success) {
        response.data = payload.data
      }
    }

    return response
  },
  async (error) => {
    const payload = error.response?.data
    if (payload && typeof payload === 'object' && payload.error && !payload.detail) {
      payload.detail = payload.error
    }

    if (error.response?.status === 401) {
      await supabase.auth.signOut()
    }

    return Promise.reject(error)
  }
)

export default api
