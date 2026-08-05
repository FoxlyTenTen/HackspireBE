import axios from 'axios'
import { clearAuth, loadAuth } from '../auth/storage'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
})

// Attach the bearer token to every request
client.interceptors.request.use((config) => {
  const auth = loadAuth()
  if (auth) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// Centralized error handling:
// - 401 with a stored session → token expired/invalid: clear and go to the
//   correct login page for the role that was active
// - normalize every failure to Error(message) using the backend's
//   {"error": "..."} shape so pages can show err.message directly
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status: number | undefined = error.response?.status
    const auth = loadAuth()
    if (status === 401 && auth) {
      clearAuth()
      window.location.href = auth.role === 'admin' ? '/administrator' : '/login'
    }
    const message: string =
      error.response?.data?.error ?? error.message ?? 'Request failed'
    return Promise.reject(new Error(message))
  },
)

export default client
