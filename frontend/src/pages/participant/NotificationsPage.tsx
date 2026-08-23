import { useCallback, useState } from 'react'
import {
  getInvitations,
  getJoinRequests,
  getNotifications,
  markNotificationRead,
  respondToJoinRequest,
} from '../../api/endpoints'
import type { JoinRequestRead, NotificationRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useMyTeam } from '../../context/MyTeamContext'
import { usePolling } from '../../hooks/usePolling'
import { formatDateTime } from '../../utils'

export default function NotificationsPage() {
  const { isLeader, refresh } = useMyTeam()
  const [notifications, setNotifications] = useState<NotificationRead[]>([])
  const [pending, setPending] = useState<JoinRequestRead[]>([])
  const [invitations, setInvitations] = useState<JoinRequestRead[]>([])
  const [error, setError] = useState<string | null>(null)

  const poll = useCallback(async () => {
    try {
      setNotifications(await getNotifications())
      setInvitations(await getInvitations())
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

  const handleMarkRead = async (notificationId: string) => {
    setNotifications((current) =>
      current.map((n) => (n.id === notificationId ? { ...n, read: true } : n)),
    )
    try {
      await markNotificationRead(notificationId)
    } catch (err) {
      setError((err as Error).message)
      await poll()
    }
  }

  const unreadCount = notifications.filter((n) => !n.read).length

  return (
    <div>
      <h1>Notifications</h1>
      <p className="muted">Updates refresh automatically every 25 seconds.</p>
      <ErrorBanner message={error} />

      <h2>Your pending invitations</h2>
      {invitations.length === 0 && <p>No pending invitations.</p>}
      <table>
        <tbody>
          {invitations.map((invitation) => (
            <tr key={invitation.id}>
              <td>
                <strong>{invitation.team_name}</strong> invited you to join
                <div className="muted">{formatDateTime(invitation.created_at)}</div>
              </td>
              <td>
                <button onClick={() => void handleRespond(invitation.id, 'approve')}>
                  Accept
                </button>{' '}
                <button
                  className="danger"
                  onClick={() => void handleRespond(invitation.id, 'reject')}
                >
                  Decline
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

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

      <h2>All notifications {unreadCount > 0 && <span className="badge">{unreadCount} unread</span>}</h2>
      {notifications.length === 0 && <p>Nothing yet.</p>}
      <ul className="notifications">
        {notifications.map((notification) => (
          <li key={notification.id} className={notification.read ? '' : 'unread'}>
            <span className="badge">{notification.type}</span> {notification.message}
            <div className="muted">{formatDateTime(notification.created_at)}</div>
            {!notification.read && (
              <button
                className="link-button"
                onClick={() => void handleMarkRead(notification.id)}
              >
                Mark as read
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
