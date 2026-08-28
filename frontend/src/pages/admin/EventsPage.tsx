import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { adminSetCountdown, getEventInfo } from '../../api/endpoints'
import ErrorBanner from '../../components/ErrorBanner'
import { useAdminAction } from '../../hooks/useAdminAction'
import { formatDateTime, localInputToIso } from '../../utils'

export default function EventsPage() {
  const [countdownValue, setCountdownValue] = useState('')
  const [currentCountdown, setCurrentCountdown] = useState<string | null>(null)
  const [countdownDescription, setCountdownDescription] = useState('')
  const { error, message, act } = useAdminAction()

  const load = useCallback(async () => {
    const info = await getEventInfo()
    setCurrentCountdown(info.countdown_at)
    setCountdownDescription(info.countdown_description ?? '')
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const handleCountdown = (e: FormEvent) => {
    e.preventDefault()
    void act(
      () => adminSetCountdown(localInputToIso(countdownValue), countdownDescription),
      'Countdown updated.',
      load,
    )
  }

  return (
    <div>
      <h1>Events</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      <section>
        <h2>Countdown (event start)</h2>
        <p className="muted">Current: {formatDateTime(currentCountdown)}</p>
        <form className="inline-form" onSubmit={handleCountdown}>
          <input
            type="datetime-local"
            value={countdownValue}
            onChange={(e) => setCountdownValue(e.target.value)}
            required
          />
          <textarea
            placeholder="Description shown under the countdown on the home page (optional)"
            value={countdownDescription}
            onChange={(e) => setCountdownDescription(e.target.value)}
            rows={3}
          />
          <button type="submit">Update countdown</button>
        </form>
      </section>
    </div>
  )
}
