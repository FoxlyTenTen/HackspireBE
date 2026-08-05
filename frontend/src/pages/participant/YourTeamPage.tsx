import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  deleteTeam,
  getTeam,
  leaveTeam,
  removeTeamMember,
  updateTeam,
} from '../../api/endpoints'
import type { TeamRead, TeamStatus } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useAuth } from '../../context/AuthContext'
import { useMyTeam } from '../../context/MyTeamContext'

const EDITABLE_STATUSES: TeamStatus[] = ['open', 'looking_for_teammates', 'closed']

export default function YourTeamPage() {
  const { teamId } = useParams<{ teamId: string }>()
  const { auth } = useAuth()
  const { refresh } = useMyTeam()
  const navigate = useNavigate()
  const [team, setTeam] = useState<TeamRead | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editCapacity, setEditCapacity] = useState(5)
  const [editStatus, setEditStatus] = useState<TeamStatus>('open')

  const load = useCallback(async () => {
    if (!teamId) return
    try {
      const detail = await getTeam(teamId)
      setTeam(detail)
      setEditName(detail.name)
      setEditCapacity(detail.capacity)
      setEditStatus(detail.status === 'full' ? 'closed' : detail.status)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [teamId])

  useEffect(() => {
    void load()
  }, [load])

  if (error && !team) return <ErrorBanner message={error} />
  if (!team || !teamId) return <p>Loading…</p>

  const userId = auth?.userId ?? ''
  const isLeader = team.leader_id === userId
  const isMember = team.members.some((m) => m.participant_id === userId)
  const locked = team.locked

  const run = async (action: () => Promise<unknown>, afterNavigate?: string) => {
    setError(null)
    try {
      await action()
      await refresh()
      if (afterNavigate) {
        navigate(afterNavigate)
      } else {
        await load()
      }
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleEdit = (e: FormEvent) => {
    e.preventDefault()
    void run(() =>
      updateTeam(teamId, { name: editName, capacity: editCapacity, status: editStatus }),
    )
  }

  return (
    <div>
      <h1>{team.name}</h1>
      <ErrorBanner message={error} />
      <p>
        <span className={`badge status-${team.status}`}>{team.status}</span>{' '}
        <span className="badge">approval: {team.approval_status}</span>{' '}
        {locked && <span className="badge locked">🔒 locked by admin approval</span>}
      </p>
      {team.admin_note && (
        <p className="admin-note">
          <strong>Admin note:</strong> {team.admin_note}
        </p>
      )}
      <p>
        Members: {team.member_count}/{team.capacity}
      </p>

      <h2>Members</h2>
      <table>
        <tbody>
          {team.members.map((member) => (
            <tr key={member.participant_id}>
              <td>
                {member.name} {member.is_leader && <span className="badge">leader</span>}
              </td>
              <td>{member.student_staff_id}</td>
              <td>
                {isLeader && !member.is_leader && !locked && (
                  <button
                    className="danger"
                    onClick={() =>
                      window.confirm(`Remove ${member.name} from the team?`) &&
                      void run(() => removeTeamMember(teamId, member.participant_id))
                    }
                  >
                    Remove
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {isMember && (
        <p>
          <Link to={`/teams/${teamId}/submission`}>View team submission →</Link>
        </p>
      )}

      {isLeader && (
        <>
          <h2>Manage team (leader)</h2>
          {locked ? (
            <p className="muted">
              This team was approved and locked by the admin — editing is disabled unless
              an admin reverts the approval.
            </p>
          ) : (
            <>
              <form className="stack-form" onSubmit={handleEdit}>
                <label>
                  Team name
                  <input value={editName} onChange={(e) => setEditName(e.target.value)} required />
                </label>
                <label>
                  Capacity (max 5, not below current members)
                  <input
                    type="number"
                    min={team.member_count}
                    max={5}
                    value={editCapacity}
                    onChange={(e) => setEditCapacity(Number(e.target.value))}
                  />
                </label>
                <label>
                  Status
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value as TeamStatus)}
                  >
                    {EDITABLE_STATUSES.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </label>
                <button type="submit">Save changes</button>
              </form>
              <p className="muted">
                Tip: add members directly from the <Link to="/participants">participants list</Link>.
              </p>
              <button
                className="danger"
                onClick={() =>
                  window.confirm(
                    'Delete the team? This is how a leader leaves — the team and its data are removed.',
                  ) && void run(() => deleteTeam(teamId), '/teams')
                }
              >
                Delete team (leader leaves)
              </button>
            </>
          )}
        </>
      )}

      {isMember && !isLeader && !locked && (
        <button
          className="danger"
          onClick={() =>
            window.confirm('Leave this team? Your slot reopens.') &&
            void run(() => leaveTeam(teamId), '/teams')
          }
        >
          Leave team
        </button>
      )}
    </div>
  )
}
