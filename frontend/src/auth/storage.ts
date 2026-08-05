// Auth persistence. localStorage is fine for this stage of the project;
// httpOnly cookies would be the production-hardened approach (immune to XSS
// token theft) but require backend cookie support.
import type { Role } from '../api/types'

const STORAGE_KEY = 'hackspire_auth'

export interface StoredAuth {
  token: string
  role: Role
  firstLogin: boolean
  userId: string
}

export function loadAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as StoredAuth) : null
  } catch {
    return null
  }
}

export function saveAuth(auth: StoredAuth): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
}

export function clearAuth(): void {
  localStorage.removeItem(STORAGE_KEY)
}

/** Extract the profile id (sub claim) from the JWT payload — decode only, no verification. */
export function decodeUserId(jwt: string): string {
  try {
    const payload = jwt.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const parsed = JSON.parse(atob(payload)) as { sub?: string }
    return parsed.sub ?? ''
  } catch {
    return ''
  }
}
