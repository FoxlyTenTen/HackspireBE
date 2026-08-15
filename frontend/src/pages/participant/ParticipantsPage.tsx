import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { addTeamMember, getParticipants } from '../../api/endpoints'
import type { ParticipantListItem } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useMyTeam } from '../../context/MyTeamContext'

export default function ParticipantsPage() {
  const { team, isLeader, refresh } = useMyTeam()
  const [participants, setParticipants] = useState<ParticipantListItem[]>([])
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const load = useCallback(
    (query?: string) =>
      getParticipants(query)
        .then(setParticipants)
        .catch((err: Error) => setError(err.message)),
    [],
  )

  useEffect(() => {
    void load()
  }, [load])

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    void load(search || undefined)
  }

  // Leaders can add unassigned participants directly (capacity permitting)
  const canAdd =
    isLeader && team !== null && !team.locked && team.member_count < team.capacity

  const handleAdd = async (participant: ParticipantListItem) => {
    if (!team) return
    setError(null)
    setMessage(null)
    try {
      await addTeamMember(team.id, participant.id)
      setMessage(`${participant.username ?? participant.name} added to ${team.name}.`)
      await refresh()
      await load(search || undefined)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <h1>Participants</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      <form className="inline-form" onSubmit={handleSearch}>
        <input
          placeholder="Search by name, username or ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Reference ID</th>
            <th>Skills / Role</th>
            <th>Status</th>
            <th>Team</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {participants.map((participant) => (
            <tr key={participant.id}>
              <td>{participant.username ?? participant.name}</td>
              <td>{participant.reference_id ?? '—'}</td>
              <td>
                {participant.technical_skills || participant.preferred_role ? (
                  <>
                    {participant.technical_skills && (
                      <div>Skills: {participant.technical_skills}</div>
                    )}
                    {participant.preferred_role && (
                      <div>Preferred role: {participant.preferred_role}</div>
                    )}
                  </>
                ) : (
                  '—'
                )}
              </td>
              <td>
                <span
                  className={`badge ${participant.status === 'no_team' ? 'status-open' : ''}`}
                >
                  {participant.status}
                </span>
              </td>
              <td>{participant.team_name ?? '—'}</td>
              <td>
                {canAdd && participant.status === 'no_team' && (
                  <button onClick={() => void handleAdd(participant)}>Add to my team</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {participants.length === 0 && <p>No participants found.</p>}
    </div>
  )
}
