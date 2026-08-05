import { useState } from 'react'
import type { FormEvent } from 'react'
import { login as apiLogin } from '../api/endpoints'
import type { Role } from '../api/types'
import { useAuth } from '../context/AuthContext'
import ErrorBanner from './ErrorBanner'

interface Props {
  expectedRole: Role
  title: string
  /** Called after a successful, role-matching login. */
  onSuccess: (firstLogin: boolean) => void
}

/**
 * Shared by both login pages. An account of the wrong role gets an inline
 * error — never a silent login into the other side.
 */
export default function LoginForm({ expectedRole, title, onSuccess }: Props) {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const response = await apiLogin(username, password)
      if (response.role !== expectedRole) {
        setError(
          expectedRole === 'participant'
            ? 'This is not a participant account — use the administrator login.'
            : 'This is not an administrator account — use the participant login.',
        )
        return
      }
      login(response)
      onSuccess(response.first_login)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-card">
      <h1>HACKSPIRE: LUMINA</h1>
      <h2>{title}</h2>
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit}>
        <label>
          Username (email or student/staff ID)
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
      </form>
    </div>
  )
}
