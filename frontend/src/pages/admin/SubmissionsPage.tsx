import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  adminGetSubmissions,
  adminSetDeadline,
  adminSubmissionsCsv,
  getEventInfo,
} from '../../api/endpoints'
import type { AdminSubmissionRow } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { downloadBlob, formatDateTime, localInputToIso } from '../../utils'

export default function AdminSubmissionsPage() {
  const [rows, setRows] = useState<AdminSubmissionRow[]>([])
  const [deadline, setDeadline] = useState<string | null>(null)
  const [deadlineValue, setDeadlineValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [submissions, info] = await Promise.all([adminGetSubmissions(), getEventInfo()])
      setRows(submissions)
      setDeadline(info.submission_deadline_at)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const handleDeadline = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      await adminSetDeadline(localInputToIso(deadlineValue))
      setMessage('Deadline updated.')
      await load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleExport = async () => {
    try {
      downloadBlob(await adminSubmissionsCsv(), 'submissions.csv')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <h1>Submissions</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      <h2>Submission deadline</h2>
      <p className="muted">Current: {formatDateTime(deadline)}</p>
      <form className="inline-form" onSubmit={(e) => void handleDeadline(e)}>
        <input
          type="datetime-local"
          value={deadlineValue}
          onChange={(e) => setDeadlineValue(e.target.value)}
          required
        />
        <button type="submit">Set deadline</button>
      </form>

      <h2>All submissions (for judges)</h2>
      <button onClick={() => void handleExport()}>Export CSV</button>
      <table>
        <thead>
          <tr>
            <th>Team</th>
            <th>Link</th>
            <th>Submitted</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.team_id}>
              <td>{row.team_name}</td>
              <td>
                <a href={row.url} target="_blank" rel="noreferrer">
                  {row.url}
                </a>
              </td>
              <td>{formatDateTime(row.submitted_at)}</td>
              <td>{formatDateTime(row.updated_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p>No submissions yet.</p>}
    </div>
  )
}
