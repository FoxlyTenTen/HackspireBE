import { useCallback, useEffect, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import {
  adminDeleteAnnouncement,
  adminDeleteMaterial,
  adminGetTeams,
  adminPostAnnouncement,
  adminPutFinalists,
  adminPutWinners,
  adminSetCountdown,
  adminSetTimeline,
  adminTimelineImportConfirm,
  adminTimelineImportPreview,
  adminUpdateAnnouncement,
  adminUploadMaterial,
  getAnnouncements,
  getEventInfo,
  getMaterials,
} from '../../api/endpoints'
import type {
  AdminTeamRead,
  AnnouncementRead,
  MaterialCategory,
  MaterialRead,
  TimelineImportPreviewResponse,
  TimelineItemWrite,
  TimelineStatus,
} from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { formatDateTime, localInputToIso, resolveFileUrl } from '../../utils'

const TIMELINE_STATUSES: TimelineStatus[] = ['TBD', 'Proposed', 'Confirmed', 'Declined']

function blankRow(order_index: number): TimelineItemWrite {
  return {
    bootcamp_name: '',
    date_label: '',
    time_session: '',
    session_type: '',
    speaker_name: '',
    speaker_bio: '',
    organization: '',
    session_description: '',
    speaker_photo_url: '',
    status: 'TBD',
    remarks: '',
    order_index,
  }
}

export default function EventContentPage() {
  const [teams, setTeams] = useState<AdminTeamRead[]>([])
  const [materials, setMaterials] = useState<MaterialRead[]>([])
  const [materialCategory, setMaterialCategory] = useState<MaterialCategory>('general')
  const [countdownValue, setCountdownValue] = useState('')
  const [currentCountdown, setCurrentCountdown] = useState<string | null>(null)
  const [timeline, setTimeline] = useState<TimelineItemWrite[]>([])
  const [timelineFile, setTimelineFile] = useState<File | null>(null)
  const [timelinePreview, setTimelinePreview] = useState<TimelineImportPreviewResponse | null>(
    null,
  )
  const [timelineBusy, setTimelineBusy] = useState(false)
  const [finalistIds, setFinalistIds] = useState<string[]>([])
  const [finalistsPublished, setFinalistsPublished] = useState(false)
  const [winnerRows, setWinnerRows] = useState<{ team_id: string; placement: string }[]>([])
  const [winnersPublished, setWinnersPublished] = useState(false)
  const [announcements, setAnnouncements] = useState<AnnouncementRead[]>([])
  const [announceTitle, setAnnounceTitle] = useState('')
  const [announceBody, setAnnounceBody] = useState('')
  const [announceImage, setAnnounceImage] = useState<File | null>(null)
  const [announceExistingImageUrl, setAnnounceExistingImageUrl] = useState<string | null>(null)
  const [editingAnnouncementId, setEditingAnnouncementId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [info, teamList, materialList, announcementList] = await Promise.all([
        getEventInfo(),
        adminGetTeams(),
        getMaterials(),
        getAnnouncements(),
      ])
      setCurrentCountdown(info.countdown_at)
      setTimeline(
        info.timeline.map((item) => ({
          bootcamp_name: item.bootcamp_name,
          date_label: item.date_label,
          time_session: item.time_session,
          session_type: item.session_type,
          speaker_name: item.speaker_name ?? '',
          speaker_bio: item.speaker_bio ?? '',
          organization: item.organization ?? '',
          session_description: item.session_description ?? '',
          speaker_photo_url: item.speaker_photo_url ?? '',
          status: item.status,
          remarks: item.remarks ?? '',
          order_index: item.order_index,
        })),
      )
      setTeams(teamList)
      setMaterials(materialList)
      setAnnouncements(announcementList)
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

  const updateRow = (index: number, patch: Partial<TimelineItemWrite>) => {
    const next = [...timeline]
    next[index] = { ...next[index], ...patch }
    setTimeline(next)
  }

  const handleTimelineSave = () => {
    const items = timeline.map((row, index) => ({ ...row, order_index: index }))
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
    await act(() => adminUploadMaterial(file, materialCategory), `Uploaded ${file.name}.`)
    e.target.value = ''
  }

  const handleTimelineFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    setTimelinePreview(null)
    setTimelineBusy(true)
    try {
      setTimelineFile(file)
      setTimelinePreview(await adminTimelineImportPreview(file))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setTimelineBusy(false)
      e.target.value = ''
    }
  }

  const handleTimelineImportConfirm = async () => {
    if (!timelinePreview) return
    const okRows: TimelineItemWrite[] = timelinePreview.rows
      .filter((row) => row.row_status === 'ok')
      .map((row) => ({
        bootcamp_name: row.bootcamp_name ?? '',
        date_label: row.date_label ?? '',
        time_session: row.time_session ?? '',
        session_type: row.session_type ?? '',
        speaker_name: row.speaker_name,
        speaker_bio: row.speaker_bio,
        organization: row.organization,
        session_description: row.session_description,
        speaker_photo_url: row.speaker_photo_url,
        status: (row.status as TimelineStatus) ?? 'TBD',
        remarks: row.remarks,
        order_index: row.order_index,
      }))
    setError(null)
    setTimelineBusy(true)
    try {
      await adminTimelineImportConfirm(okRows)
      setTimelinePreview(null)
      setTimelineFile(null)
      setMessage('Timeline imported.')
      await load()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setTimelineBusy(false)
    }
  }

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

  const cancelEditAnnouncement = () => {
    setEditingAnnouncementId(null)
    setAnnounceTitle('')
    setAnnounceBody('')
    setAnnounceImage(null)
    setAnnounceExistingImageUrl(null)
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

        <h3>Import from Excel</h3>
        <p className="muted">
          Step 1: choose an .xlsx file (columns: bootcamp_name, date_label, time_session,
          session_type, plus optional speaker_name, speaker_bio, organization,
          session_description, speaker_photo_url, status, remarks, order_index) to preview.
          Confirming replaces the entire timeline.
        </p>
        <input
          type="file"
          accept=".xlsx"
          onChange={(e) => void handleTimelineFile(e)}
          disabled={timelineBusy}
        />
        {timelinePreview && (
          <>
            <p>
              <strong>{timelinePreview.ok_count}</strong> row(s) ready ·{' '}
              <strong>{timelinePreview.flagged_count}</strong> flagged (will be skipped)
            </p>
            <table>
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Bootcamp</th>
                  <th>Date</th>
                  <th>Session</th>
                  <th>Status</th>
                  <th>Issues</th>
                </tr>
              </thead>
              <tbody>
                {timelinePreview.rows.map((row) => (
                  <tr
                    key={row.row_number}
                    className={row.row_status === 'flagged' ? 'flagged-row' : ''}
                  >
                    <td>{row.row_number}</td>
                    <td>{row.bootcamp_name ?? '—'}</td>
                    <td>{row.date_label ?? '—'}</td>
                    <td>{row.time_session ?? '—'}</td>
                    <td>
                      <span
                        className={`badge ${row.row_status === 'ok' ? 'status-open' : 'locked'}`}
                      >
                        {row.row_status}
                      </span>
                    </td>
                    <td>{row.issues.join('; ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button
              onClick={() => void handleTimelineImportConfirm()}
              disabled={timelineBusy || timelinePreview.ok_count === 0}
            >
              Confirm import ({timelinePreview.ok_count} item
              {timelinePreview.ok_count === 1 ? '' : 's'}) — replaces entire timeline
            </button>{' '}
            <button
              type="button"
              onClick={() => {
                setTimelinePreview(null)
                setTimelineFile(null)
              }}
            >
              Cancel
            </button>
          </>
        )}
        {timelineFile && !timelinePreview && timelineBusy && <p>Parsing…</p>}

        <h3>Manual edit</h3>
        {timeline.map((row, index) => (
          <div className="timeline-row-block" key={index}>
            <div className="timeline-row">
              <input
                placeholder="Bootcamp name"
                value={row.bootcamp_name}
                onChange={(e) => updateRow(index, { bootcamp_name: e.target.value })}
              />
              <input
                placeholder="Date label (e.g. 13-15 Oct 2026)"
                value={row.date_label}
                onChange={(e) => updateRow(index, { date_label: e.target.value })}
              />
              <input
                placeholder="Time & session"
                value={row.time_session}
                onChange={(e) => updateRow(index, { time_session: e.target.value })}
              />
              <input
                placeholder="Session type (e.g. Keynote)"
                value={row.session_type}
                onChange={(e) => updateRow(index, { session_type: e.target.value })}
              />
              <select
                value={row.status}
                onChange={(e) => updateRow(index, { status: e.target.value as TimelineStatus })}
              >
                {TIMELINE_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div className="timeline-row">
              <input
                placeholder="Speaker name"
                value={row.speaker_name ?? ''}
                onChange={(e) => updateRow(index, { speaker_name: e.target.value })}
              />
              <input
                placeholder="Organization"
                value={row.organization ?? ''}
                onChange={(e) => updateRow(index, { organization: e.target.value })}
              />
              <input
                placeholder="Speaker photo URL"
                value={row.speaker_photo_url ?? ''}
                onChange={(e) => updateRow(index, { speaker_photo_url: e.target.value })}
              />
            </div>
            <div className="timeline-row">
              <input
                placeholder="Session description"
                value={row.session_description ?? ''}
                onChange={(e) => updateRow(index, { session_description: e.target.value })}
              />
              <input
                placeholder="Speaker bio"
                value={row.speaker_bio ?? ''}
                onChange={(e) => updateRow(index, { speaker_bio: e.target.value })}
              />
              <input
                placeholder="Remarks (admin-only)"
                value={row.remarks ?? ''}
                onChange={(e) => updateRow(index, { remarks: e.target.value })}
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
          </div>
        ))}
        <button type="button" onClick={() => setTimeline([...timeline, blankRow(timeline.length)])}>
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
        <select
          value={materialCategory}
          onChange={(e) => setMaterialCategory(e.target.value as MaterialCategory)}
        >
          <option value="general">General</option>
          <option value="submission_template">Submission template</option>
        </select>{' '}
        <input type="file" onChange={(e) => void handleUpload(e)} />
        <ul>
          {materials.map((material) => (
            <li key={material.id}>
              {material.file_name}{' '}
              <span className="badge">{material.category}</span>{' '}
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
                  void act(() => adminDeleteAnnouncement(a.id), 'Announcement deleted.')
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
