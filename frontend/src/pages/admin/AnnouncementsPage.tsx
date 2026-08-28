import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  adminBroadcastNotification,
  adminDeleteAnnouncement,
  adminPostAnnouncement,
  adminUpdateAnnouncement,
  getAnnouncements,
} from '../../api/endpoints'
import type { AnnouncementRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useAdminAction } from '../../hooks/useAdminAction'
import { formatDateTime, resolveFileUrl } from '../../utils'

export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState<AnnouncementRead[]>([])
  const [announceTitle, setAnnounceTitle] = useState('')
  const [announceBody, setAnnounceBody] = useState('')
  const [announceImage, setAnnounceImage] = useState<File | null>(null)
  const [announceExistingImageUrl, setAnnounceExistingImageUrl] = useState<string | null>(null)
  const [editingAnnouncementId, setEditingAnnouncementId] = useState<string | null>(null)
  const [broadcastMessage, setBroadcastMessage] = useState('')
  const { error, message, act } = useAdminAction()

  const load = useCallback(async () => {
    setAnnouncements(await getAnnouncements())
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const handleAnnounce = (e: FormEvent) => {
    e.preventDefault()
    void act(
      () =>
        editingAnnouncementId
          ? adminUpdateAnnouncement(editingAnnouncementId, {
              title: announceTitle,
              body: announceBody,
              image: announceImage,
            })
          : adminPostAnnouncement(announceTitle, announceBody, announceImage),
      editingAnnouncementId ? 'Announcement updated.' : 'Announcement posted — all participants notified.',
      load,
    ).then(() => {
      setAnnounceTitle('')
      setAnnounceBody('')
      setAnnounceImage(null)
      setAnnounceExistingImageUrl(null)
      setEditingAnnouncementId(null)
    })
  }

  const startEditAnnouncement = (a: AnnouncementRead) => {
    setEditingAnnouncementId(a.id)
    setAnnounceTitle(a.title)
    setAnnounceBody(a.body)
    setAnnounceImage(null)
    setAnnounceExistingImageUrl(a.image_url ?? null)
  }

  const handleBroadcast = (e: FormEvent) => {
    e.preventDefault()
    void act(
      () => adminBroadcastNotification(broadcastMessage),
      'Notification sent to all participants.',
    ).then(() => setBroadcastMessage(''))
  }

  const cancelEditAnnouncement = () => {
    setEditingAnnouncementId(null)
    setAnnounceTitle('')
    setAnnounceBody('')
    setAnnounceImage(null)
    setAnnounceExistingImageUrl(null)
  }

  return (
    <div>
      <h1>Announcements</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      <section>
        <h2>Quick notification</h2>
        <p className="muted">
          Notification-only — no title/image, nothing saved, doesn't appear below. Just lands in
          every participant's notification feed. For anything that should persist and be
          browsable, use Announcements instead.
        </p>
        <form className="inline-form" onSubmit={handleBroadcast}>
          <input
            placeholder="e.g. Reminder: submissions close in 1 hour!"
            value={broadcastMessage}
            onChange={(e) => setBroadcastMessage(e.target.value)}
            maxLength={500}
            required
          />
          <button type="submit">Send to all participants</button>
        </form>
      </section>

      <section>
        <h2>Announcements</h2>
        <form className="stack-form" onSubmit={handleAnnounce}>
          <label>
            Title
            <input
              value={announceTitle}
              onChange={(e) => setAnnounceTitle(e.target.value)}
              required
            />
          </label>
          <label>
            Body
            <textarea
              value={announceBody}
              onChange={(e) => setAnnounceBody(e.target.value)}
              rows={3}
              required
            />
          </label>
          <label>
            Image (optional)
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setAnnounceImage(e.target.files?.[0] ?? null)}
            />
          </label>
          {announceExistingImageUrl && !announceImage && (
            <p className="muted">
              Current image:{' '}
              <a href={resolveFileUrl(announceExistingImageUrl) ?? ''} target="_blank" rel="noreferrer">
                view
              </a>{' '}
              (choose a new file to replace it)
            </p>
          )}
          <button type="submit">
            {editingAnnouncementId ? 'Save changes' : 'Post (notifies all participants)'}
          </button>{' '}
          {editingAnnouncementId && (
            <button type="button" onClick={cancelEditAnnouncement}>
              Cancel edit
            </button>
          )}
        </form>

        <ul className="announcements">
          {announcements.map((a) => (
            <li key={a.id} className="announcement-card">
              <strong>{a.title}</strong>
              {a.image_url && (
                <img
                  src={resolveFileUrl(a.image_url) ?? ''}
                  alt={a.title}
                  className="announcement-image"
                />
              )}
              <p>{a.body}</p>
              <div className="muted">
                Posted {formatDateTime(a.posted_at)}
                {a.updated_at && <> · updated {formatDateTime(a.updated_at)}</>}
              </div>
              <button onClick={() => startEditAnnouncement(a)}>Edit</button>{' '}
              <button
                className="danger"
                onClick={() =>
                  window.confirm(`Delete announcement "${a.title}"?`) &&
                  void act(() => adminDeleteAnnouncement(a.id), 'Announcement deleted.', load)
                }
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
