import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  downloadMaterial,
  getEventInfo,
  getFinalists,
  getMaterials,
  getNotifications,
  getWinners,
} from '../../api/endpoints'
import type {
  EventInfo,
  FinalistRead,
  MaterialRead,
  NotificationRead,
  WinnerRead,
} from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { usePolling } from '../../hooks/usePolling'
import { formatDateTime } from '../../utils'

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

export default function HomePage() {
  const [info, setInfo] = useState<EventInfo | null>(null)
  const [materials, setMaterials] = useState<MaterialRead[]>([])
  const [finalists, setFinalists] = useState<FinalistRead[]>([])
  const [winners, setWinners] = useState<WinnerRead[]>([])
  const [notifications, setNotifications] = useState<NotificationRead[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([getEventInfo(), getMaterials(), getFinalists(), getWinners()])
      .then(([eventInfo, materialList, finalistList, winnerList]) => {
        setInfo(eventInfo)
        setMaterials(materialList)
        setFinalists(finalistList)
        setWinners(winnerList)
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  const pollNotifications = useCallback(
    () => getNotifications().then(setNotifications).catch(() => {}),
    [],
  )
  usePolling(pollNotifications, 25_000)

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
      setError(err instanceof Error ? err.message : 'Download failed')
    }
  }

  if (error) return <ErrorBanner message={error} />
  if (!info) return <p>Loading…</p>

  return (
    <div className="grid-2">
      <section>
        <h1>{info.name}</h1>
        <p className="tagline">{info.tagline}</p>
        <p>
          <strong>Venue:</strong> {info.venue}
        </p>
        {info.countdown_at && <Countdown target={info.countdown_at} />}
        {info.submission_deadline_at && (
          <p>
            <strong>Submission deadline:</strong> {formatDateTime(info.submission_deadline_at)}
          </p>
        )}

        <h2>Timeline</h2>
        {info.timeline.length === 0 && <p>Agenda coming soon.</p>}
        <ul className="timeline">
          {info.timeline.map((item) => (
            <li key={item.id}>
              <strong>{item.time_label}</strong> — {item.title}
              {item.description && <div className="muted">{item.description}</div>}
            </li>
          ))}
        </ul>

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
  )
}
