import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getNotifications, markNotificationRead } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import type { NotificationRead } from '../api/types'
import { formatDateTime } from '../utils'
import { BellIcon } from './icons'

export default function NotificationBell() {
  const queryClient = useQueryClient()
  const { data: notifications = [] } = useQuery({
    queryKey: queryKeys.notifications,
    queryFn: getNotifications,
    refetchInterval: 25_000,
  })
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onClickOutside = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [open])

  const unreadCount = notifications.filter((n) => !n.read).length

  const handleMarkRead = async (id: string) => {
    queryClient.setQueryData<NotificationRead[]>(queryKeys.notifications, (current) =>
      current?.map((n) => (n.id === id ? { ...n, read: true } : n)),
    )
    try {
      await markNotificationRead(id)
    } catch {
      await queryClient.invalidateQueries({ queryKey: queryKeys.notifications })
    }
  }

  return (
    <div className="notification-bell" ref={rootRef}>
      <button
        type="button"
        className="bell-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      >
        <BellIcon />
        {unreadCount > 0 && <span className="bell-badge">{unreadCount}</span>}
      </button>
      {open && (
        <div className="notification-dropdown">
          <div className="notification-dropdown-header">
            <strong>Notifications</strong>
            <Link to="/notifications" onClick={() => setOpen(false)}>
              View all
            </Link>
          </div>
          {notifications.length === 0 && <p className="muted">Nothing yet.</p>}
          <ul className="notifications">
            {notifications.slice(0, 6).map((n) => (
              <li key={n.id} className={n.read ? '' : 'unread'}>
                <span className="badge">{n.type}</span> {n.message}
                <div className="muted">{formatDateTime(n.created_at)}</div>
                {!n.read && (
                  <button className="link-button" onClick={() => void handleMarkRead(n.id)}>
                    Mark as read
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
