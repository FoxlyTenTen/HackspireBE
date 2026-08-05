import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { changePassword } from '../../api/endpoints'
import ErrorBanner from '../../components/ErrorBanner'
import { useAuth } from '../../context/AuthContext'

/**
 * Forced first-login password change. After success the backend clears
 * first_login and expects a fresh login, so we log out client-side and
 * return to the appropriate login page.
 */
export default function ChangePasswordPage() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (!auth) return <Navigate to="/login" replace />

  const loginPath = auth.role === 'admin' ? '/administrator' : '/login'

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (newPassword !== confirm) {
      setError('Passwords do not match')
      return
    }
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    setBusy(true)
    try {
      await changePassword(newPassword)
      logout()
      alert('Password changed — please log in again with your new password.')
      navigate(loginPath, { replace: true })
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  return (
    <div className="login-card">
      <h1>HACKSPIRE: LUMINA</h1>
      <h2>Set a new password</h2>
      <p>You must change your password before continuing.</p>
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit}>
        <label>
          New password
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            autoFocus
          />
        </label>
        <label>
          Confirm new password
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? 'Saving…' : 'Change password'}
        </button>
      </form>
    </div>
  )
}
