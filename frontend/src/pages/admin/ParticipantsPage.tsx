import { useCallback, useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import {
  adminGetParticipants,
  adminImportConfirm,
  adminImportPreview,
  adminParticipantsCsv,
  adminResetPassword,
} from '../../api/endpoints'
import type {
  AdminParticipantsResponse,
  ImportConfirmResponse,
  ImportPreviewResponse,
} from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { downloadBlob, formatDateTime } from '../../utils'

export default function AdminParticipantsPage() {
  const [data, setData] = useState<AdminParticipantsResponse | null>(null)
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null)
  const [confirmResult, setConfirmResult] = useState<ImportConfirmResponse | null>(null)
  const [resetInfo, setResetInfo] = useState<{ name: string; password: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(
    () => adminGetParticipants().then(setData).catch((err: Error) => setError(err.message)),
    [],
  )

  useEffect(() => {
    void load()
  }, [load])

  const handleFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    setPreview(null)
    setConfirmResult(null)
    setBusy(true)
    try {
      setPreview(await adminImportPreview(file))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
      e.target.value = '' // allow re-selecting the same file
    }
  }

  const handleConfirm = async () => {
    if (!preview) return
    const okRows = preview.rows
      .filter((row) => row.status === 'ok')
      .map((row) => ({
        name: row.name ?? '',
        email: row.email ?? '',
        student_staff_id: row.student_staff_id ?? '',
      }))
    setError(null)
    setBusy(true)
    try {
      setConfirmResult(await adminImportConfirm(okRows))
      setPreview(null)
      await load()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleExport = async () => {
    try {
      downloadBlob(await adminParticipantsCsv(), 'participants.csv')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleReset = async (participantId: string, name: string) => {
    if (!window.confirm(`Reset password for ${name}? Their current password stops working.`))
      return
    setError(null)
    try {
      const result = await adminResetPassword(participantId)
      setResetInfo({ name, password: result.temporary_password })
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <h1>Participants</h1>
      <ErrorBanner message={error} />

      <h2>Excel import</h2>
      <p className="muted">
        Step 1: choose an .xlsx file (columns: name, email, student_staff_id) to preview.
        Nothing is written until you confirm. Initial password = student/staff ID.
      </p>
      <input type="file" accept=".xlsx" onChange={(e) => void handleFile(e)} disabled={busy} />

      {preview && (
        <>
          <p>
            <strong>{preview.ok_count}</strong> row(s) ready ·{' '}
            <strong>{preview.flagged_count}</strong> flagged (will be skipped)
          </p>
          <table>
            <thead>
              <tr>
                <th>Row</th>
                <th>Name</th>
                <th>Email</th>
                <th>ID</th>
                <th>Status</th>
                <th>Issues</th>
              </tr>
            </thead>
            <tbody>
              {preview.rows.map((row) => (
                <tr key={row.row_number} className={row.status === 'flagged' ? 'flagged-row' : ''}>
                  <td>{row.row_number}</td>
                  <td>{row.name ?? '—'}</td>
                  <td>{row.email ?? '—'}</td>
                  <td>{row.student_staff_id ?? '—'}</td>
                  <td>
                    <span className={`badge ${row.status === 'ok' ? 'status-open' : 'locked'}`}>
                      {row.status}
                    </span>
                  </td>
                  <td>{row.issues.join('; ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={() => void handleConfirm()} disabled={busy || preview.ok_count === 0}>
            Confirm import ({preview.ok_count} account{preview.ok_count === 1 ? '' : 's'})
          </button>
        </>
      )}

      {confirmResult && (
        <div className="success-banner">
          Created {confirmResult.created} account(s), skipped {confirmResult.skipped}.
          {confirmResult.skipped_rows.length > 0 && (
            <ul>
              {confirmResult.skipped_rows.map((row) => (
                <li key={row.row_number}>
                  {row.email ?? row.name ?? `row ${row.row_number}`}: {row.issues.join('; ')}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {resetInfo && (
        <div className="success-banner">
          Temporary password for <strong>{resetInfo.name}</strong>:{' '}
          <code>{resetInfo.password}</code>{' '}
          <button onClick={() => void navigator.clipboard.writeText(resetInfo.password)}>
            Copy
          </button>{' '}
          — they must change it on next login.
        </div>
      )}

      <h2>
        All participants{' '}
        {data && (
          <span className="muted">
            ({data.count}/{data.cap} — {data.remaining} slots left)
          </span>
        )}
      </h2>
      <button onClick={() => void handleExport()}>Export CSV</button>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>ID</th>
            <th>First login pending</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data?.participants.map((participant) => (
            <tr key={participant.id}>
              <td>{participant.name}</td>
              <td>{participant.email}</td>
              <td>{participant.student_staff_id}</td>
              <td>{participant.first_login ? 'yes' : 'no'}</td>
              <td>{formatDateTime(participant.created_at)}</td>
              <td>
                <button onClick={() => void handleReset(participant.id, participant.name)}>
                  Reset password
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {data && data.participants.length === 0 && <p>No participants imported yet.</p>}
    </div>
  )
}
