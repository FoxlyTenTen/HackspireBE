import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { setPasswordWithToken, verifyOtp } from '../api/endpoints'
import ErrorBanner from '../components/ErrorBanner'

/**
 * Landing page for Supabase Auth invite / password-recovery email links
 * (redirect_to points here). Supabase's hosted /auth/v1/verify endpoint
 * verifies the link server-side THEN redirects here — historically as a hash
 * fragment (`#access_token=...&type=...`), but some project configs instead
 * pass `?token_hash=...&type=...` for the client to exchange itself via
 * POST /auth/verify-otp. Both are checked so this works either way.
 */
export default function AcceptInvitePage() {
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [linkType, setLinkType] = useState<string | null>(null)

  const hashParams = useMemo(
    () => new URLSearchParams(window.location.hash.replace(/^#/, '')),
    [],
  )
  const queryParams = useMemo(() => new URLSearchParams(window.location.search), [])

  useEffect(() => {
    const hashError = hashParams.get('error_description')
    const queryError = queryParams.get('error_description')
    if (hashError || queryError) {
      setError((hashError ?? queryError ?? '').replace(/\+/g, ' '))
      setLoading(false)
      return
    }

    const hashToken = hashParams.get('access_token')
    if (hashToken) {
      setAccessToken(hashToken)
      setLinkType(hashParams.get('type'))
      setLoading(false)
      return
    }

    const tokenHash = queryParams.get('token_hash')
    const type = queryParams.get('type')
    if (tokenHash && type) {
      verifyOtp(tokenHash, type)
        .then((session) => {
          setAccessToken(session.jwt)
          setLinkType(session.type)
        })
        .catch((err: Error) => setError(err.message))
        .finally(() => setLoading(false))
      return
    }

    setLoading(false)
  }, [hashParams, queryParams])

  if (loading) {
    return (
      <div className="login-card">
        <h1>HACKSPIRE: LUMINA</h1>
        <p>Verifying your link…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="login-card">
        <h1>HACKSPIRE: LUMINA</h1>
        <ErrorBanner message={error} />
        <p>
          The link may have expired or already been used. Ask an admin to
          re-invite you, or use “Forgot password” on the{' '}
          <Link to="/login">login page</Link>.
        </p>
      </div>
    )
  }

  if (!accessToken) {
    return (
      <div className="login-card">
        <h1>HACKSPIRE: LUMINA</h1>
        <ErrorBanner message="This page only works when opened from an email link." />
        <Link to="/login">Go to login</Link>
      </div>
    )
  }

  const isInvite = linkType === 'invite' || linkType === 'signup'

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    setBusy(true)
    try {
      await setPasswordWithToken(accessToken, password)
      alert('Password set — log in with your email and new password.')
      navigate('/login', { replace: true })
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  return (
    <div className="login-card">
      <h1>HACKSPIRE: LUMINA</h1>
      <h2>{isInvite ? 'Activate your account' : 'Set a new password'}</h2>
      <p>
        {isInvite
          ? 'Welcome! Choose a password to finish setting up your account.'
          : 'Choose a new password for your account.'}
      </p>
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit}>
        <label>
          New password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
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
          {busy ? 'Saving…' : isInvite ? 'Activate account' : 'Set password'}
        </button>
      </form>
    </div>
  )
}
