import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import {
  createSubmission,
  downloadMaterial,
  getEventInfo,
  getMaterials,
  getSubmission,
  getTeam,
  updateSubmission,
} from '../../api/endpoints'
import type { MaterialRead, SubmissionRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useAuth } from '../../context/AuthContext'
import { formatDateTime, isValidGdriveUrl, isValidGithubUrl } from '../../utils'

export default function SubmissionPage() {
  const { teamId } = useParams<{ teamId: string }>()
  const { auth } = useAuth()
  const [submission, setSubmission] = useState<SubmissionRead | null>(null)
  const [deadline, setDeadline] = useState<string | null>(null)
  const [isMember, setIsMember] = useState(false)
  const [githubUrl, setGithubUrl] = useState('')
  const [gdriveUrl, setGdriveUrl] = useState('')
  const [templates, setTemplates] = useState<MaterialRead[]>([])
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)

  const load = useCallback(async () => {
    if (!teamId) return
    setError(null)
    try {
      const info = await getEventInfo()
      setDeadline(info.submission_deadline_at)
      const team = await getTeam(teamId)
      const userId = auth?.userId ?? ''
      setIsMember(team.members.some((m) => m.participant_id === userId))
      const materials = await getMaterials()
      setTemplates(materials.filter((m) => m.category === 'submission_template'))
      try {
        const existing = await getSubmission(teamId)
        setSubmission(existing)
        setGithubUrl(existing.github_url ?? '')
        setGdriveUrl(existing.gdrive_url ?? '')
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
    if (!githubUrl && !gdriveUrl) {
      setError('Provide at least a GitHub link or a Google Drive link')
      return
    }
    if (githubUrl && !isValidGithubUrl(githubUrl)) {
      setError('GitHub link must be a well-formed github.com URL')
      return
    }
    if (gdriveUrl && !isValidGdriveUrl(gdriveUrl)) {
      setError('Google Drive link must be a well-formed drive.google.com/docs.google.com URL')
      return
    }
    const body = { github_url: githubUrl || null, gdrive_url: gdriveUrl || null }
    try {
      const saved = submission
        ? await updateSubmission(teamId, body)
        : await createSubmission(teamId, body)
      setSubmission(saved)
      setMessage('Submission saved.')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleDownloadTemplate = async (material: MaterialRead) => {
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
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <h1>Team Submission</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      {templates.length > 0 && (
        <div className="admin-note">
          <strong>Submission template{templates.length > 1 ? 's' : ''}:</strong>{' '}
          {templates.map((material, index) => (
            <span key={material.id}>
              {index > 0 && ', '}
              <a
                href={material.file_url}
                onClick={(e) => {
                  e.preventDefault()
                  void handleDownloadTemplate(material)
                }}
              >
                {material.file_name}
              </a>
            </span>
          ))}
        </div>
      )}

      {deadline && (
        <p>
          <strong>Deadline:</strong> {formatDateTime(deadline)}{' '}
          {deadlinePassed && <span className="badge locked">passed</span>}
        </p>
      )}

      {submission ? (
        <p>
          {submission.github_url && (
            <>
              GitHub:{' '}
              <a href={submission.github_url} target="_blank" rel="noreferrer">
                {submission.github_url}
              </a>
              <br />
            </>
          )}
          {submission.gdrive_url && (
            <>
              Drive (infographic + pitch deck):{' '}
              <a href={submission.gdrive_url} target="_blank" rel="noreferrer">
                {submission.gdrive_url}
              </a>
              <br />
            </>
          )}
          <span className="muted">
            Submitted {formatDateTime(submission.submitted_at)} · last updated{' '}
            {formatDateTime(submission.updated_at)}
          </span>
        </p>
      ) : (
        <p>No submission yet.</p>
      )}

      {isMember && !deadlinePassed && (
        <form className="stack-form" onSubmit={handleSubmit}>
          <label>
            GitHub link
            <input
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/your-team/project"
            />
          </label>
          <label>
            Google Drive link (infographic + pitch deck)
            <input
              value={gdriveUrl}
              onChange={(e) => setGdriveUrl(e.target.value)}
              placeholder="https://drive.google.com/drive/folders/..."
            />
          </label>
          <button type="submit">{submission ? 'Update links' : 'Submit links'}</button>
        </form>
      )}
      {isMember && deadlinePassed && (
        <p className="muted">The deadline has passed — the links can no longer be changed.</p>
      )}
      {!isMember && <p className="muted">Only team members can submit or edit the links.</p>}
    </div>
  )
}
