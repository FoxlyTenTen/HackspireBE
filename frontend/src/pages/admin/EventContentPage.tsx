import { useCallback, useEffect, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import {
  adminDeleteMaterial,
  adminGetTeams,
  adminPostAnnouncement,
  adminPutFinalists,
  adminPutWinners,
  adminSetCountdown,
  adminSetTimeline,
  adminUploadMaterial,
  getEventInfo,
  getMaterials,
} from '../../api/endpoints'
import type { AdminTeamRead, MaterialRead, TimelineItemWrite } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { formatDateTime, localInputToIso } from '../../utils'

interface TimelineRow {
  time_label: string
  title: string
  description: string
}

export default function EventContentPage() {
  const [teams, setTeams] = useState<AdminTeamRead[]>([])
  const [materials, setMaterials] = useState<MaterialRead[]>([])
  const [countdownValue, setCountdownValue] = useState('')
  const [currentCountdown, setCurrentCountdown] = useState<string | null>(null)
  const [timeline, setTimeline] = useState<TimelineRow[]>([])
  const [finalistIds, setFinalistIds] = useState<string[]>([])
  const [finalistsPublished, setFinalistsPublished] = useState(false)
  const [winnerRows, setWinnerRows] = useState<{ team_id: string; placement: string }[]>([])
  const [winnersPublished, setWinnersPublished] = useState(false)
  const [announceTitle, setAnnounceTitle] = useState('')
  const [announceBody, setAnnounceBody] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [info, teamList, materialList] = await Promise.all([
        getEventInfo(),
        adminGetTeams(),
        getMaterials(),
      ])
      setCurrentCountdown(info.countdown_at)
      setTimeline(
        info.timeline.map((item) => ({
          time_label: item.time_label,
          title: item.title,
          description: item.description ?? '',
        })),
      )
      setTeams(teamList)
      setMaterials(materialList)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const act = async (action: () => Promise<unknown>, successMessage: string) => {
    setError(null)
    setMessage(null)
    try {
      await action()
      setMessage(successMessage)
      await load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleCountdown = (e: FormEvent) => {
    e.preventDefault()
    void act(() => adminSetCountdown(localInputToIso(countdownValue)), 'Countdown updated.')
  }

  const handleTimelineSave = () => {
    const items: TimelineItemWrite[] = timeline.map((row, index) => ({
      time_label: row.time_label,
      title: row.title,
      description: row.description || null,
      order_index: index,
    }))
    void act(() => adminSetTimeline(items), 'Timeline saved.')
  }

  const moveRow = (index: number, delta: number) => {
    const next = [...timeline]
    const target = index + delta
    if (target < 0 || target >= next.length) return
    ;[next[index], next[target]] = [next[target], next[index]]
    setTimeline(next)
  }

  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    await act(() => adminUploadMaterial(file), `Uploaded ${file.name}.`)
    e.target.value = ''
  }

  const handleAnnounce = (e: FormEvent) => {
    e.preventDefault()
    void act(
      () => adminPostAnnouncement(announceTitle, announceBody),
      'Announcement posted — all participants notified.',
    ).then(() => {
      setAnnounceTitle('')
      setAnnounceBody('')
    })
  }

  return (
    <div>
      <h1>Event Content</h1>
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
          <button type="submit">Update countdown</button>
        </form>
      </section>

      <section>
        <h2>Timeline / agenda</h2>
        {timeline.map((row, index) => (
          <div className="timeline-row" key={index}>
            <input
              placeholder="09:00"
              value={row.time_label}
              onChange={(e) => {
                const next = [...timeline]
                next[index] = { ...row, time_label: e.target.value }
                setTimeline(next)
              }}
            />
            <input
              placeholder="Title"
              value={row.title}
              onChange={(e) => {
                const next = [...timeline]
                next[index] = { ...row, title: e.target.value }
                setTimeline(next)
              }}
            />
            <input
              placeholder="Description (optional)"
              value={row.description}
              onChange={(e) => {
                const next = [...timeline]
                next[index] = { ...row, description: e.target.value }
                setTimeline(next)
              }}
            />
            <button type="button" onClick={() => moveRow(index, -1)}>↑</button>
            <button type="button" onClick={() => moveRow(index, 1)}>↓</button>
            <button
              type="button"
              className="danger"
              onClick={() => setTimeline(timeline.filter((_, i) => i !== index))}
            >
              ✕
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() => setTimeline([...timeline, { time_label: '', title: '', description: '' }])}
        >
          + Add item
        </button>{' '}
        <button type="button" onClick={handleTimelineSave}>
          Save timeline
        </button>
      </section>

      <section>
        <h2>Finalists</h2>
        <p className="muted">Select teams, then publish to make them visible to participants.</p>
        {teams.map((team) => (
          <label key={team.id} className="checkbox">
            <input
              type="checkbox"
              checked={finalistIds.includes(team.id)}
              onChange={(e) =>
                setFinalistIds(
                  e.target.checked
                    ? [...finalistIds, team.id]
                    : finalistIds.filter((id) => id !== team.id),
                )
              }
            />
            {team.name}
          </label>
        ))}
        <label className="checkbox">
          <input
            type="checkbox"
            checked={finalistsPublished}
            onChange={(e) => setFinalistsPublished(e.target.checked)}
          />
          Published (visible to participants)
        </label>
        <button
          type="button"
          onClick={() =>
            void act(
              () => adminPutFinalists(finalistIds, finalistsPublished),
              'Finalist list saved.',
            )
          }
        >
          Save finalists
        </button>
      </section>

      <section>
        <h2>Winners</h2>
        {winnerRows.map((row, index) => (
          <div className="timeline-row" key={index}>
            <select
              value={row.team_id}
              onChange={(e) => {
                const next = [...winnerRows]
                next[index] = { ...row, team_id: e.target.value }
                setWinnerRows(next)
              }}
            >
              <option value="">— pick a team —</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
            <input
              placeholder="Placement (e.g. champion)"
              value={row.placement}
              onChange={(e) => {
                const next = [...winnerRows]
                next[index] = { ...row, placement: e.target.value }
                setWinnerRows(next)
              }}
            />
            <button
              type="button"
              className="danger"
              onClick={() => setWinnerRows(winnerRows.filter((_, i) => i !== index))}
            >
              ✕
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() => setWinnerRows([...winnerRows, { team_id: '', placement: '' }])}
        >
          + Add winner
        </button>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={winnersPublished}
            onChange={(e) => setWinnersPublished(e.target.checked)}
          />
          Published (visible to participants)
        </label>
        <button
          type="button"
          onClick={() =>
            void act(
              () =>
                adminPutWinners(
                  winnerRows.filter((row) => row.team_id && row.placement),
                  winnersPublished,
                ),
              'Winner list saved.',
            )
          }
        >
          Save winners
        </button>
      </section>

      <section>
        <h2>Materials</h2>
        <input type="file" onChange={(e) => void handleUpload(e)} />
        <ul>
          {materials.map((material) => (
            <li key={material.id}>
              {material.file_name}{' '}
              <span className="muted">({formatDateTime(material.uploaded_at)})</span>{' '}
              <button
                className="danger"
                onClick={() =>
                  window.confirm(`Remove ${material.file_name}?`) &&
                  void act(() => adminDeleteMaterial(material.id), 'Material removed.')
                }
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Post announcement</h2>
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
          <button type="submit">Post (notifies all participants)</button>
        </form>
      </section>
    </div>
  )
}
