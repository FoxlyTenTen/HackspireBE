import { useEffect, useState } from 'react'
import { getAnnouncements } from '../../api/endpoints'
import type { AnnouncementRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { formatDateTime, resolveFileUrl } from '../../utils'

export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState<AnnouncementRead[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getAnnouncements()
      .then(setAnnouncements)
      .catch((err: Error) => setError(err.message))
  }, [])

  return (
    <div>
      <h1>Announcements</h1>
      <ErrorBanner message={error} />
      {announcements.length === 0 && <p>No announcements yet.</p>}
      <ul className="announcements">
        {announcements.map((a) => (
          <li key={a.id} className="announcement-card">
            <h2>{a.title}</h2>
            {a.image_url && (
              <img src={resolveFileUrl(a.image_url) ?? ''} alt={a.title} className="announcement-image" />
            )}
            <p>{a.body}</p>
            <div className="muted">
              Posted {formatDateTime(a.posted_at)}
              {a.updated_at && <> · updated {formatDateTime(a.updated_at)}</>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
