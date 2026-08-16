import axios from 'axios'
import type { AxiosRequestConfig } from 'axios'
import { clearAuth, loadAuth, saveAuth } from '../auth/storage'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

const client = axios.create({ baseURL: BASE_URL })

// Attach the bearer token to every request
client.interceptors.request.use((config) => {
  const auth = loadAuth()
  if (auth) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// Supabase access tokens expire (~1h). One refresh is shared between
// concurrent 401s so parallel requests don't each burn the refresh token
// (Supabase rotates it on every use).
let refreshing: Promise<string | null> | null = null

async function refreshSession(): Promise<string | null> {
  const auth = loadAuth()
  if (!auth?.refreshToken) return null
  try {
    // Raw axios: going through `client` would loop the interceptors.
    const { data } = await axios.post<{ jwt: string; refresh_token: string }>(
      `${BASE_URL}/auth/refresh`,
      { refresh_token: auth.refreshToken },
    )
    saveAuth({ ...auth, token: data.jwt, refreshToken: data.refresh_token })
    return data.jwt
  } catch {
    return null
  }
}

// Centralized error handling:
// - 401 with a stored session → try one token refresh and retry the request;
//   if that fails, clear and go to the correct login page for the active role
// - normalize every failure to Error(message) using the backend's
//   {"error": "..."} shape so pages can show err.message directly
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status: number | undefined = error.response?.status
    const auth = loadAuth()
    const original = error.config as (AxiosRequestConfig & { _retried?: boolean }) | undefined
    if (status === 401 && auth && original && !original._retried) {
      refreshing = refreshing ?? refreshSession().finally(() => (refreshing = null))
      const newToken = await refreshing
      if (newToken) {
        original._retried = true
        original.headers = { ...original.headers, Authorization: `Bearer ${newToken}` }
        return client(original)
      }
      clearAuth()
      window.location.href = auth.role === 'admin' ? '/administrator' : '/login'
    }
    const message: string =
      error.response?.data?.error ?? error.message ?? 'Request failed'
    return Promise.reject(new Error(message))
  },
)

export default client
