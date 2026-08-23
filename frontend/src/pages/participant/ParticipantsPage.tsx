import { useState } from 'react'
import type { FormEvent } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getParticipants, inviteParticipant } from '../../api/endpoints'
import { queryKeys } from '../../api/queryKeys'
import type { ParticipantListItem } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useMyTeam } from '../../context/MyTeamContext'

export default function ParticipantsPage() {
  const { team, isLeader } = useMyTeam()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [submittedSearch, setSubmittedSearch] = useState<string | undefined>(undefined)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const { data: participants = [], error: loadError } = useQuery({
    queryKey: queryKeys.participants(submittedSearch),
    queryFn: () => getParticipants(submittedSearch),
  })

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    setSubmittedSearch(search || undefined)
  }

  // Leaders can invite unassigned participants (capacity permitting) — the
  // participant must accept before they actually join
  const canAdd =
    isLeader && team !== null && !team.locked && team.member_count < team.capacity

  const handleInvite = async (participant: ParticipantListItem) => {
    if (!team) return
    setError(null)
    setMessage(null)
    try {
      await inviteParticipant(team.id, participant.id)
      setMessage(`Invite sent to ${participant.username ?? participant.name}.`)
      await queryClient.invalidateQueries({ queryKey: queryKeys.participants(submittedSearch) })
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <h1>Participants</h1>
      <ErrorBanner message={error ?? (loadError as Error | null)?.message ?? null} />
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
                  <button onClick={() => void handleInvite(participant)}>Invite to my team</button>
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
