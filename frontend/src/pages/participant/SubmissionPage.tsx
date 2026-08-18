import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import {
  createSubmission,
  downloadMaterial,
  getEventInfo,
  getFinalists,
  getMaterials,
  getSubmission,
  getTeam,
  updateSubmission,
} from '../../api/endpoints'
import type { MaterialRead, SubmissionRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useAuth } from '../../context/AuthContext'
import { formatDateTime, isValidGithubUrl, isValidLinkUrl } from '../../utils'

interface RoundSectionProps {
  round: 1 | 2
  teamId: string
  title: string
  submission: SubmissionRead | null
  onSaved: (submission: SubmissionRead) => void
  deadline: string | null
  isMember: boolean
  isApproved: boolean
  eligible: boolean
  ineligibleMessage?: string
}

function SubmissionRoundSection({
  round,
  teamId,
  title,
  submission,
  onSaved,
  deadline,
  isMember,
  isApproved,
  eligible,
  ineligibleMessage,
}: RoundSectionProps) {
  const [githubUrl, setGithubUrl] = useState('')
  const [infographicUrl, setInfographicUrl] = useState('')
  const [pitchDeckUrl, setPitchDeckUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    setGithubUrl(submission?.github_url ?? '')
    setInfographicUrl(submission?.infographic_url ?? '')
    setPitchDeckUrl(submission?.pitch_deck_url ?? '')
  }, [submission])

  const deadlinePassed = deadline !== null && new Date(deadline).getTime() < Date.now()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    if (!githubUrl && !infographicUrl && !pitchDeckUrl) {
      setError('Provide at least a GitHub link, an infographic link, or a pitch deck link')
      return
    }
    if (githubUrl && !isValidGithubUrl(githubUrl)) {
      setError('GitHub link must be a well-formed github.com URL')
      return
    }
    if (infographicUrl && !isValidLinkUrl(infographicUrl)) {
      setError('Infographic link must be a well-formed https URL')
      return
    }
    if (pitchDeckUrl && !isValidLinkUrl(pitchDeckUrl)) {
      setError('Pitch deck link must be a well-formed https URL')
      return
    }
    const body = {
      github_url: githubUrl || null,
      infographic_url: infographicUrl || null,
      pitch_deck_url: pitchDeckUrl || null,
    }
    try {
      const saved = submission
        ? await updateSubmission(teamId, round, body)
        : await createSubmission(teamId, round, body)
      onSaved(saved)
      setMessage('Submission saved.')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <section>
      <h2>{title}</h2>
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
          {submission.github_url && (
            <>
              GitHub:{' '}
              <a href={submission.github_url} target="_blank" rel="noreferrer">
                {submission.github_url}
              </a>
              <br />
            </>
          )}
          {submission.infographic_url && (
            <>
              Infographic:{' '}
              <a href={submission.infographic_url} target="_blank" rel="noreferrer">
                {submission.infographic_url}
              </a>
              <br />
            </>
          )}
          {submission.pitch_deck_url && (
            <>
              Pitch deck:{' '}
              <a href={submission.pitch_deck_url} target="_blank" rel="noreferrer">
                {submission.pitch_deck_url}
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

      {isMember && !isApproved && (
        <p className="muted">
          Your team must be approved by an admin before you can submit links.
        </p>
      )}
      {isMember && isApproved && !eligible && (
        <p className="muted">{ineligibleMessage}</p>
      )}
      {isMember && isApproved && eligible && !deadlinePassed && (
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
            Infographic link
            <input
              value={infographicUrl}
              onChange={(e) => setInfographicUrl(e.target.value)}
              placeholder="https://drive.google.com/file/d/..."
            />
          </label>
          <label>
            Pitch deck link
            <input
              value={pitchDeckUrl}
              onChange={(e) => setPitchDeckUrl(e.target.value)}
              placeholder="https://drive.google.com/file/d/..."
            />
          </label>
          <button type="submit">{submission ? 'Update links' : 'Submit links'}</button>
        </form>
      )}
      {isMember && isApproved && eligible && deadlinePassed && (
        <p className="muted">The deadline has passed — the links can no longer be changed.</p>
      )}
      {!isMember && <p className="muted">Only team members can submit or edit the links.</p>}
    </section>
  )
}

export default function SubmissionPage() {
  const { teamId } = useParams<{ teamId: string }>()
  const { auth } = useAuth()
  const [submission1, setSubmission1] = useState<SubmissionRead | null>(null)
  const [submission2, setSubmission2] = useState<SubmissionRead | null>(null)
  const [deadline1, setDeadline1] = useState<string | null>(null)
  const [deadline2, setDeadline2] = useState<string | null>(null)
  const [isMember, setIsMember] = useState(false)
  const [isApproved, setIsApproved] = useState(false)
  const [isFinalist, setIsFinalist] = useState(false)
  const [templates, setTemplates] = useState<MaterialRead[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)

  const load = useCallback(async () => {
    if (!teamId) return
    setError(null)
    try {
      const info = await getEventInfo()
      setDeadline1(info.submission_deadline_at)
      setDeadline2(info.round2_submission_deadline_at)
      const team = await getTeam(teamId)
      const userId = auth?.userId ?? ''
      setIsMember(team.members.some((m) => m.participant_id === userId))
      setIsApproved(team.approval_status === 'approved')
      const finalists = await getFinalists()
      setIsFinalist(finalists.some((f) => f.team_id === teamId))
      const materials = await getMaterials()
      setTemplates(materials.filter((m) => m.category === 'submission_template'))
      try {
        setSubmission1(await getSubmission(teamId, 1))
      } catch {
        setSubmission1(null) // 404 — nothing submitted yet
      }
      try {
        setSubmission2(await getSubmission(teamId, 2))
      } catch {
        setSubmission2(null) // 404 — nothing submitted yet
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

  if (!teamId) return null
  if (!loaded) return <p>Loading…</p>

  return (
    <div>
      <h1>Team Submission</h1>
      <ErrorBanner message={error} />

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

      <SubmissionRoundSection
        round={1}
        teamId={teamId}
        title="Round 1 — Qualifying submission"
        submission={submission1}
        onSaved={setSubmission1}
        deadline={deadline1}
        isMember={isMember}
        isApproved={isApproved}
        eligible
      />

      <SubmissionRoundSection
        round={2}
        teamId={teamId}
        title="Round 2 — Finalist submission"
        submission={submission2}
        onSaved={setSubmission2}
        deadline={deadline2}
        isMember={isMember}
        isApproved={isApproved}
        eligible={isFinalist}
        ineligibleMessage="Round 2 opens once finalists are announced."
      />
    </div>
  )
}
