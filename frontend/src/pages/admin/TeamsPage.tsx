import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  adminApproveTeam,
  adminDeleteTeam,
  adminRejectTeam,
  adminUpdateTeam,
  getTeam,
} from '../../api/endpoints'
import { adminGetTeams } from '../../api/endpoints'
import type { AdminTeamRead, TeamMemberRead, TeamStatus } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'

const ALL_STATUSES: TeamStatus[] = ['open', 'looking_for_teammates', 'closed', 'full']

interface EditState {
  teamId: string
  name: string
  capacity: number
  status: TeamStatus
  leaderId: string
  locked: boolean
  members: TeamMemberRead[]
}

export default function AdminTeamsPage() {
  const [teams, setTeams] = useState<AdminTeamRead[]>([])
  const [edit, setEdit] = useState<EditState | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(
    () => adminGetTeams().then(setTeams).catch((err: Error) => setError(err.message)),
    [],
  )

  useEffect(() => {
    void load()
  }, [load])

  const run = async (action: () => Promise<unknown>) => {
    setError(null)
    try {
      await action()
      await load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const openEdit = async (team: AdminTeamRead) => {
    setError(null)
    try {
      const detail = await getTeam(team.id)
      setEdit({
        teamId: team.id,
        name: team.name,
        capacity: team.capacity,
        status: team.status,
        leaderId: team.leader_id,
        locked: team.locked,
        members: detail.members,
      })
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleEditSave = (e: FormEvent) => {
    e.preventDefault()
    if (!edit) return
    void run(() =>
      adminUpdateTeam(edit.teamId, {
        name: edit.name,
        capacity: edit.capacity,
        status: edit.status,
        leader_id: edit.leaderId,
        locked: edit.locked,
      }),
    ).then(() => setEdit(null))
  }

  const handleReject = (team: AdminTeamRead) => {
    const note = window.prompt(
      `Reject "${team.name}" — optional note for the team (leave empty for none):`,
    )
    if (note === null) return // cancelled
    void run(() => adminRejectTeam(team.id, note || undefined))
  }

  return (
    <div>
      <h1>Teams</h1>
      <ErrorBanner message={error} />
      <table>
        <thead>
          <tr>
            <th>Ref</th>
            <th>Name</th>
            <th>Leader</th>
            <th>Members</th>
            <th>Status</th>
            <th>Approval</th>
            <th>Submission</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {teams.map((team) => (
            <tr key={team.id}>
              <td>{team.reference_id ?? '—'}</td>
              <td>
                {team.name} {team.locked && '🔒'}
                {team.admin_note && <div className="muted">note: {team.admin_note}</div>}
              </td>
              <td>{team.leader_name}</td>
              <td>
                {team.member_count}/{team.capacity}
              </td>
              <td>
                <span className={`badge status-${team.status}`}>{team.status}</span>
              </td>
              <td>
                <span className="badge">{team.approval_status}</span>
              </td>
              <td>{team.has_submission ? '✅' : '—'}</td>
              <td className="actions">
                {team.approval_status !== 'approved' && (
                  <button onClick={() => void run(() => adminApproveTeam(team.id))}>
                    Approve
                  </button>
                )}
                <button onClick={() => handleReject(team)}>Reject</button>
                <button onClick={() => void openEdit(team)}>Edit</button>
                <button
                  className="danger"
                  onClick={() =>
                    window.confirm(`Force-delete "${team.name}"? Members become unassigned.`) &&
                    void run(() => adminDeleteTeam(team.id))
                  }
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {teams.length === 0 && <p>No teams yet.</p>}

      {edit && (
        <form className="stack-form edit-panel" onSubmit={handleEditSave}>
          <h2>Edit team</h2>
          <label>
            Name
            <input
              value={edit.name}
              onChange={(e) => setEdit({ ...edit, name: e.target.value })}
              required
            />
          </label>
          <label>
            Capacity (1–5)
            <input
              type="number"
              min={1}
              max={5}
              value={edit.capacity}
              onChange={(e) => setEdit({ ...edit, capacity: Number(e.target.value) })}
            />
          </label>
          <label>
            Status
            <select
              value={edit.status}
              onChange={(e) => setEdit({ ...edit, status: e.target.value as TeamStatus })}
            >
              {ALL_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>
          <label>
            Leader (reassign to a current member)
            <select
              value={edit.leaderId}
              onChange={(e) => setEdit({ ...edit, leaderId: e.target.value })}
            >
              {edit.members.map((member) => (
                <option key={member.participant_id} value={member.participant_id}>
                  {member.name} ({member.student_staff_id})
                </option>
              ))}
            </select>
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={edit.locked}
              onChange={(e) => setEdit({ ...edit, locked: e.target.checked })}
            />
            Locked (unchecking an approved team reverts its approval to pending)
          </label>
          <div>
            <button type="submit">Save</button>{' '}
            <button type="button" onClick={() => setEdit(null)}>
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
