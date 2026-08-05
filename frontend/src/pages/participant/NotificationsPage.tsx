import { useCallback, useState } from 'react'
import { getJoinRequests, getNotifications, respondToJoinRequest } from '../../api/endpoints'
import type { JoinRequestRead, NotificationRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useMyTeam } from '../../context/MyTeamContext'
import { usePolling } from '../../hooks/usePolling'
import { formatDateTime } from '../../utils'

export default function NotificationsPage() {
  const { isLeader, refresh } = useMyTeam()
  const [notifications, setNotifications] = useState<NotificationRead[]>([])
  const [pending, setPending] = useState<JoinRequestRead[]>([])
  const [error, setError] = useState<string | null>(null)

  const poll = useCallback(async () => {
    try {
      setNotifications(await getNotifications())
      if (isLeader) {
        setPending(await getJoinRequests())
      }
    } catch {
      // polling errors are transient; don't spam the banner
    }
  }, [isLeader])

  usePolling(poll, 25_000)

  const handleRespond = async (requestId: string, decision: 'approve' | 'reject') => {
    setError(null)
    try {
      await respondToJoinRequest(requestId, decision)
      await refresh()
      await poll()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <h1>Notifications</h1>
      <p className="muted">Updates refresh automatically every 25 seconds.</p>
      <ErrorBanner message={error} />

      {isLeader && (
        <>
          <h2>Pending join requests for your team</h2>
          {pending.length === 0 && <p>No pending requests.</p>}
          <table>
            <tbody>
              {pending.map((request) => (
                <tr key={request.id}>
                  <td>
                    <strong>{request.participant_name}</strong> wants to join{' '}
                    {request.team_name}
                    <div className="muted">{formatDateTime(request.created_at)}</div>
                  </td>
                  <td>
                    <button onClick={() => void handleRespond(request.id, 'approve')}>
                      Approve
                    </button>{' '}
                    <button
                      className="danger"
                      onClick={() => void handleRespond(request.id, 'reject')}
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <h2>All notifications</h2>
      {notifications.length === 0 && <p>Nothing yet.</p>}
      <ul className="notifications">
        {notifications.map((notification) => (
          <li key={notification.id}>
            <span className="badge">{notification.type}</span> {notification.message}
            <div className="muted">{formatDateTime(notification.created_at)}</div>
          </li>
        ))}
      </ul>
    </div>
  )
}
