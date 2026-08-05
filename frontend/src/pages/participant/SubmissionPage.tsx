import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import {
  createSubmission,
  getEventInfo,
  getSubmission,
  getTeam,
  updateSubmission,
} from '../../api/endpoints'
import type { SubmissionRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useAuth } from '../../context/AuthContext'
import { formatDateTime, isValidSubmissionUrl } from '../../utils'

export default function SubmissionPage() {
  const { teamId } = useParams<{ teamId: string }>()
  const { auth } = useAuth()
  const [submission, setSubmission] = useState<SubmissionRead | null>(null)
  const [deadline, setDeadline] = useState<string | null>(null)
  const [isLeader, setIsLeader] = useState(false)
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)

  const load = useCallback(async () => {
    if (!teamId) return
    setError(null)
    try {
      const info = await getEventInfo()
      setDeadline(info.submission_deadline_at)
      // Leader check via team detail (submission GET itself is member-only)
      const team = await getTeam(teamId)
      setIsLeader(team.leader_id === (auth?.userId ?? ''))
      try {
        const existing = await getSubmission(teamId)
        setSubmission(existing)
        setUrl(existing.url)
      } catch {
        setSubmission(null) // 404 — nothing submitted yet
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoaded(true)
    }
  }, [teamId, auth?.userId])

  useEffect(() => {
    void load()
  }, [load])

  if (!teamId) return null
  if (!loaded) return <p>Loading…</p>

  const deadlinePassed = deadline !== null && new Date(deadline).getTime() < Date.now()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    if (!isValidSubmissionUrl(url)) {
      setError('URL must be a well-formed GitHub or Google Drive link')
      return
    }
    try {
      const saved = submission
        ? await updateSubmission(teamId, url)
        : await createSubmission(teamId, url)
      setSubmission(saved)
      setMessage('Submission saved.')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <h1>Team Submission</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      {deadline && (
        <p>
          <strong>Deadline:</strong> {formatDateTime(deadline)}{' '}
          {deadlinePassed && <span className="badge locked">passed</span>}
        </p>
      )}

      {submission ? (
        <p>
          Current link:{' '}
          <a href={submission.url} target="_blank" rel="noreferrer">
            {submission.url}
          </a>
          <br />
          <span className="muted">
            Submitted {formatDateTime(submission.submitted_at)} · last updated{' '}
            {formatDateTime(submission.updated_at)}
          </span>
        </p>
      ) : (
        <p>No submission yet.</p>
      )}

      {isLeader && !deadlinePassed && (
        <form className="stack-form" onSubmit={handleSubmit}>
          <label>
            GitHub or Google Drive link
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/your-team/project"
              required
            />
          </label>
          <button type="submit">{submission ? 'Update link' : 'Submit link'}</button>
        </form>
      )}
      {isLeader && deadlinePassed && (
        <p className="muted">The deadline has passed — the link can no longer be changed.</p>
      )}
      {!isLeader && <p className="muted">Only the team leader can submit or edit the link.</p>}
    </div>
  )
}
