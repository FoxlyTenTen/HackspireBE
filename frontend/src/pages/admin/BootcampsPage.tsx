import { useCallback, useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import {
  adminSetTimeline,
  adminTimelineImportConfirm,
  adminTimelineImportPreview,
  adminUpdateTimelineItem,
  getEventInfo,
} from '../../api/endpoints'
import type {
  TimelineImportPreviewResponse,
  TimelineItemWrite,
  TimelineStatus,
} from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useAdminAction } from '../../hooks/useAdminAction'
import { resolveFileUrl } from '../../utils'

const TIMELINE_STATUSES: TimelineStatus[] = ['TBD', 'Proposed', 'Confirmed', 'Declined']

type TimelineRow = TimelineItemWrite & { id?: string }

function blankRow(order_index: number): TimelineRow {
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
    zoom_link: '',
  }
}

export default function BootcampsPage() {
  const [timeline, setTimeline] = useState<TimelineRow[]>([])
  const [timelineFile, setTimelineFile] = useState<File | null>(null)
  const [timelinePreview, setTimelinePreview] = useState<TimelineImportPreviewResponse | null>(
    null,
  )
  const [timelineBusy, setTimelineBusy] = useState(false)
  const { error, message, setError, setMessage, act } = useAdminAction()

  const load = useCallback(async () => {
    const info = await getEventInfo()
    setTimeline(
      info.timeline.map((item) => ({
        id: item.id,
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
        zoom_link: item.zoom_link ?? '',
        material_file_url: item.material_file_url,
        material_file_name: item.material_file_name,
      })),
    )
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const updateRow = (index: number, patch: Partial<TimelineRow>) => {
    const next = [...timeline]
    next[index] = { ...next[index], ...patch }
    setTimeline(next)
  }

  const handleTimelineSave = () => {
    const items = timeline.map((row, index) => {
      const { id: _id, ...rest } = row
      return { ...rest, order_index: index }
    })
    void act(() => adminSetTimeline(items), 'Timeline saved.', load)
  }

  const handleTimelineMaterialUpload = async (id: string, e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    await act(() => adminUpdateTimelineItem(id, {}, file), `Attached ${file.name}.`, load)
    e.target.value = ''
  }

  const handleTimelineMaterialRemove = (id: string) => {
    void act(() => adminUpdateTimelineItem(id, {}, null, true), 'Material removed.', load)
  }

  const moveRow = (index: number, delta: number) => {
    const next = [...timeline]
    const target = index + delta
    if (target < 0 || target >= next.length) return
    ;[next[index], next[target]] = [next[target], next[index]]
    setTimeline(next)
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

  return (
    <div>
      <h1>Bootcamps</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

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
            </div>
            <div className="timeline-row">
              <input
                placeholder="Zoom link (optional)"
                value={row.zoom_link ?? ''}
                onChange={(e) => updateRow(index, { zoom_link: e.target.value })}
              />
              {row.id && (
                <>
                  {row.material_file_url ? (
                    <span className="muted">
                      Material:{' '}
                      <a href={resolveFileUrl(row.material_file_url) ?? ''} target="_blank" rel="noreferrer">
                        {row.material_file_name ?? 'view'}
                      </a>{' '}
                      <button
                        type="button"
                        className="danger"
                        onClick={() => handleTimelineMaterialRemove(row.id!)}
                      >
                        Remove
                      </button>
                    </span>
                  ) : (
                    <input
                      type="file"
                      onChange={(e) => void handleTimelineMaterialUpload(row.id!, e)}
                    />
                  )}
                </>
              )}
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
    </div>
  )
}
