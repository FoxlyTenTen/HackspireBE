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

type RoundFilter = 'all' | 1 | 2

export default function AdminSubmissionsPage() {
  const [rows, setRows] = useState<AdminSubmissionRow[]>([])
  const [roundFilter, setRoundFilter] = useState<RoundFilter>('all')
  const [deadline1, setDeadline1] = useState<string | null>(null)
  const [deadline2, setDeadline2] = useState<string | null>(null)
  const [deadline1Value, setDeadline1Value] = useState('')
  const [deadline2Value, setDeadline2Value] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const load = useCallback(async (filter: RoundFilter) => {
    try {
      const [submissions, info] = await Promise.all([
        adminGetSubmissions(filter === 'all' ? undefined : filter),
        getEventInfo(),
      ])
      setRows(submissions)
      setDeadline1(info.submission_deadline_at)
      setDeadline2(info.round2_submission_deadline_at)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  useEffect(() => {
    void load(roundFilter)
  }, [load, roundFilter])

  const handleDeadline = (round: 1 | 2, value: string) => async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      await adminSetDeadline(round, localInputToIso(value))
      setMessage(`Round ${round} deadline updated.`)
      await load(roundFilter)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleExport = async () => {
    try {
      downloadBlob(
        await adminSubmissionsCsv(roundFilter === 'all' ? undefined : roundFilter),
        'submissions.csv',
      )
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <h1>Submissions</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      <h2>Round 1 deadline (qualifying)</h2>
      <p className="muted">Current: {formatDateTime(deadline1)}</p>
      <form className="inline-form" onSubmit={handleDeadline(1, deadline1Value)}>
        <input
          type="datetime-local"
          value={deadline1Value}
          onChange={(e) => setDeadline1Value(e.target.value)}
          required
        />
        <button type="submit">Set round 1 deadline</button>
      </form>

      <h2>Round 2 deadline (finalists)</h2>
      <p className="muted">Current: {formatDateTime(deadline2)}</p>
      <form className="inline-form" onSubmit={handleDeadline(2, deadline2Value)}>
        <input
          type="datetime-local"
          value={deadline2Value}
          onChange={(e) => setDeadline2Value(e.target.value)}
          required
        />
        <button type="submit">Set round 2 deadline</button>
      </form>

      <h2>All submissions (for judges)</h2>
      <div className="inline-form">
        <select
          value={roundFilter}
          onChange={(e) =>
            setRoundFilter(e.target.value === 'all' ? 'all' : (Number(e.target.value) as 1 | 2))
          }
        >
          <option value="all">All rounds</option>
          <option value={1}>Round 1</option>
          <option value={2}>Round 2</option>
        </select>
        <button onClick={() => void handleExport()}>Export CSV</button>
      </div>
      <table>
        <thead>
          <tr>
            <th>Round</th>
            <th>Ref</th>
            <th>Team</th>
            <th>GitHub</th>
            <th>Infographic</th>
            <th>Pitch Deck</th>
            <th>Submitted</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.team_id}-${row.round}`}>
              <td>{row.round}</td>
              <td>{row.team_reference_id ?? '—'}</td>
              <td>{row.team_name}</td>
              <td>
                {row.github_url ? (
                  <a href={row.github_url} target="_blank" rel="noreferrer">
                    {row.github_url}
                  </a>
                ) : (
                  '—'
                )}
              </td>
              <td>
                {row.infographic_url ? (
                  <a href={row.infographic_url} target="_blank" rel="noreferrer">
                    {row.infographic_url}
                  </a>
                ) : (
                  '—'
                )}
              </td>
              <td>
                {row.pitch_deck_url ? (
                  <a href={row.pitch_deck_url} target="_blank" rel="noreferrer">
                    {row.pitch_deck_url}
                  </a>
                ) : (
                  '—'
                )}
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
