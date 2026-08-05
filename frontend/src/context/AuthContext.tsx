import { createContext, useCallback, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { LoginResponse } from '../api/types'
import { clearAuth, decodeUserId, loadAuth, saveAuth } from '../auth/storage'
import type { StoredAuth } from '../auth/storage'

interface AuthContextValue {
  auth: StoredAuth | null
  login: (response: LoginResponse) => StoredAuth
  markPasswordChanged: () => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<StoredAuth | null>(() => loadAuth())

  const login = useCallback((response: LoginResponse): StoredAuth => {
    const next: StoredAuth = {
      token: response.jwt,
      role: response.role,
      firstLogin: response.first_login,
      userId: decodeUserId(response.jwt),
    }
    saveAuth(next)
    setAuth(next)
    return next
  }, [])

  const markPasswordChanged = useCallback(() => {
    setAuth((current) => {
      if (!current) return current
      const next = { ...current, firstLogin: false }
      saveAuth(next)
      return next
    })
  }, [])

  const logout = useCallback(() => {
    clearAuth()
    setAuth(null)
  }, [])

  return (
    <AuthContext.Provider value={{ auth, login, markPasswordChanged, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}
