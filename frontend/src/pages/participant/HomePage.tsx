import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  downloadMaterial,
  getAnnouncements,
  getEventInfo,
  getFinalists,
  getMaterials,
  getNotifications,
  getWinners,
} from '../../api/endpoints'
import { queryKeys } from '../../api/queryKeys'
import type { MaterialRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { AnnouncementsIcon, ChevronRightIcon } from '../../components/icons'
import { formatDateTime, resolveFileUrl } from '../../utils'

function Countdown({ target }: { target: string }) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])
  const diff = new Date(target).getTime() - now
  if (diff <= 0) return <p className="countdown">The event has started! 🚀</p>
  const days = Math.floor(diff / 86_400_000)
  const hours = Math.floor((diff % 86_400_000) / 3_600_000)
  const minutes = Math.floor((diff % 3_600_000) / 60_000)
  const seconds = Math.floor((diff % 60_000) / 1000)
  return (
    <p className="countdown">
      Starts in {days}d {hours}h {minutes}m {seconds}s
    </p>
  )
}

type TimelineTab = 'session' | 'materials' | 'zoom'

export default function HomePage() {
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const [expandedAnnouncementIds, setExpandedAnnouncementIds] = useState<Set<string>>(new Set())
  const [timelineTab, setTimelineTab] = useState<TimelineTab>('session')

  const toggleAnnouncement = (id: string) => {
    setExpandedAnnouncementIds((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const eventInfoQuery = useQuery({ queryKey: ['event-info'], queryFn: getEventInfo })
  const materialsQuery = useQuery({ queryKey: ['materials'], queryFn: getMaterials })
  const finalistsQuery = useQuery({ queryKey: ['finalists'], queryFn: getFinalists })
  const winnersQuery = useQuery({ queryKey: ['winners'], queryFn: getWinners })
  const announcementsQuery = useQuery({ queryKey: ['announcements'], queryFn: getAnnouncements })
  const { data: notifications = [] } = useQuery({
    queryKey: queryKeys.notifications,
    queryFn: getNotifications,
    refetchInterval: 25_000,
  })

  const info = eventInfoQuery.data ?? null
  const materials = (materialsQuery.data ?? []).filter((m) => m.category === 'general')
  const finalists = finalistsQuery.data ?? []
  const winners = winnersQuery.data ?? []
  const announcements = announcementsQuery.data ?? []
  const loadError =
    eventInfoQuery.error ??
    materialsQuery.error ??
    finalistsQuery.error ??
    winnersQuery.error ??
    announcementsQuery.error

  const handleDownload = async (material: MaterialRead) => {
    try {
      const blob = await downloadMaterial(material.id)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = material.file_name
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : 'Download failed')
    }
  }

  if (downloadError) return <ErrorBanner message={downloadError} />
  if (loadError) return <ErrorBanner message={(loadError as Error).message} />
  if (!info) return <p>Loading…</p>

  const latestAnnouncements = announcements.slice(0, 3)
  const visibleTimeline = info.timeline.filter((item) => item.status !== 'Declined')
  const materialItems = visibleTimeline.filter((item) => item.material_file_url)
  const zoomItems = visibleTimeline.filter((item) => item.zoom_link)

  return (
    <div>
      <section className="page-header">
        <h1>{info.name}</h1>
        <p className="tagline">{info.tagline}</p>
        <p>
          <strong>Venue:</strong> {info.venue}
        </p>
        {info.countdown_at && <Countdown target={info.countdown_at} />}
        {info.countdown_description && (
          <p className="countdown-description">{info.countdown_description}</p>
        )}
        {info.submission_deadline_at && (
          <p>
            <strong>Submission deadline:</strong> {formatDateTime(info.submission_deadline_at)}
          </p>
        )}
      </section>

      {latestAnnouncements.length > 0 && (
        <section className="dash-announcements">
          <div className="dash-announcements-header">
            <h2>
              <AnnouncementsIcon /> Announcements
            </h2>
            <Link to="/announcements" className="view-all-link">
              View all
            </Link>
          </div>
          <div className="dash-announcements-scroll">
            {latestAnnouncements.map((a) => {
              const isOpen = expandedAnnouncementIds.has(a.id)
              return (
                <div key={a.id} className="announcement-row">
                  <button
                    type="button"
                    className="announcement-row-header"
                    onClick={() => toggleAnnouncement(a.id)}
                    aria-expanded={isOpen}
                  >
                    <span className={`announcement-chevron${isOpen ? ' open' : ''}`}>
                      <ChevronRightIcon />
                    </span>
                    <span className="announcement-row-headtext">
                      <span className="announcement-row-title">{a.title}</span>
                      <span className="muted announcement-row-meta">
                        Posted by {a.posted_by} · {formatDateTime(a.posted_at)}
                      </span>
                    </span>
                  </button>
                  <div className={`announcement-row-body${isOpen ? '' : ' clamped'}`}>
                    {isOpen && a.image_url && (
                      <img
                        src={resolveFileUrl(a.image_url) ?? ''}
                        alt={a.title}
                        className="dash-announcement-image"
                      />
                    )}
                    <p>{a.body}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      <section className="dash-timeline">
        <h2>Timeline</h2>
        <div className="section-tabs">
          <button
            type="button"
            className={timelineTab === 'session' ? 'active' : ''}
            onClick={() => setTimelineTab('session')}
          >
            Session
          </button>
          <button
            type="button"
            className={timelineTab === 'materials' ? 'active' : ''}
            onClick={() => setTimelineTab('materials')}
          >
            Resource Materials
          </button>
          <button
            type="button"
            className={timelineTab === 'zoom' ? 'active' : ''}
            onClick={() => setTimelineTab('zoom')}
          >
            Zoom Link
          </button>
        </div>

        {timelineTab === 'session' && (
          <>
            {visibleTimeline.length === 0 && <p>Agenda coming soon.</p>}
            <ul className="timeline">
              {visibleTimeline.map((item) => (
                <li key={item.id}>
                  <strong>{item.bootcamp_name}</strong> — {item.date_label}
                  <div>{item.time_session}</div>
                  <span className="badge">{item.session_type}</span>
                  {item.speaker_name && (
                    <div className="muted">
                      {item.speaker_name}
                      {item.organization && <> · {item.organization}</>}
                    </div>
                  )}
                  {item.session_description && (
                    <div className="muted">{item.session_description}</div>
                  )}
                </li>
              ))}
            </ul>
          </>
        )}

        {timelineTab === 'materials' && (
          <>
            {materialItems.length === 0 && <p>No resource materials yet.</p>}
            <ul className="timeline">
              {materialItems.map((item) => (
                <li key={item.id}>
                  <strong>{item.bootcamp_name}</strong> — {item.date_label}
                  <div className="timeline-actions">
                    <a
                      href={resolveFileUrl(item.material_file_url) ?? ''}
                      target="_blank"
                      rel="noreferrer"
                      className="btn-link"
                    >
                      {item.material_file_name ?? 'Download material'}
                    </a>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}

        {timelineTab === 'zoom' && (
          <>
            {zoomItems.length === 0 && <p>No Zoom links yet.</p>}
            <ul className="timeline">
              {zoomItems.map((item) => (
                <li key={item.id}>
                  <strong>{item.bootcamp_name}</strong> — {item.date_label}
                  <div>{item.time_session}</div>
                  <div className="timeline-actions">
                    <a href={item.zoom_link ?? ''} target="_blank" rel="noreferrer" className="btn-link">
                      Join session
                    </a>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <div className="grid-2">
        <section>
          <h2>Prize Pool — {info.prize_pool.total}</h2>
          <ul>
            {info.prize_pool.breakdown.map((prize) => (
              <li key={prize.placement}>
                {prize.placement}: {prize.prize}
              </li>
            ))}
          </ul>

          <h2>Sponsors</h2>
          <ul>
            {info.sponsors.map((sponsor) => (
              <li key={sponsor.name}>
                {sponsor.name} <span className="badge">{sponsor.tier}</span>
              </li>
            ))}
          </ul>

          <h2>Contact</h2>
          <ul>
            {Object.entries(info.contact).map(([key, value]) => (
              <li key={key}>
                {key}: {value}
              </li>
            ))}
          </ul>
        </section>

        <section>
          {winners.length > 0 && (
            <>
              <h2>🏆 Winners</h2>
              <ul>
                {winners.map((winner) => (
                  <li key={winner.id}>
                    <strong>{winner.placement}</strong>: {winner.team_name}
                  </li>
                ))}
              </ul>
            </>
          )}
          {finalists.length > 0 && (
            <>
              <h2>Finalists</h2>
              <ul>
                {finalists.map((finalist) => (
                  <li key={finalist.id}>{finalist.team_name}</li>
                ))}
              </ul>
            </>
          )}

          <h2>Materials</h2>
          {materials.length === 0 && <p>No materials yet.</p>}
          <ul>
            {materials.map((material) => (
              <li key={material.id}>
                <a
                  href={material.file_url}
                  onClick={(e) => {
                    e.preventDefault()
                    handleDownload(material)
                  }}
                >
                  {material.file_name}
                </a>{' '}
                <span className="muted">({formatDateTime(material.uploaded_at)})</span>
              </li>
            ))}
          </ul>

          <h2>
            Notifications <Link to="/notifications">(all)</Link>
          </h2>
          {notifications.length === 0 && <p>Nothing yet.</p>}
          <ul className="notifications">
            {notifications.slice(0, 5).map((notification) => (
              <li key={notification.id}>
                <span className="badge">{notification.type}</span> {notification.message}
                <div className="muted">{formatDateTime(notification.created_at)}</div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
