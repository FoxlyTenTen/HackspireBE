import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createTeam, listTeams, requestToJoin } from '../../api/endpoints'
import type { TeamListItem } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useAuth } from '../../context/AuthContext'
import { useMyTeam } from '../../context/MyTeamContext'

export default function TeamsPage() {
  const { auth } = useAuth()
  const isAdmin = auth?.role === 'admin'
  const { team: myTeam, refresh } = useMyTeam()
  const navigate = useNavigate()
  const [teams, setTeams] = useState<TeamListItem[]>([])
  const [search, setSearch] = useState('')
  const [newName, setNewName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const load = useCallback(
    (query?: string) =>
      listTeams(query).then(setTeams).catch((err: Error) => setError(err.message)),
    [],
  )

  useEffect(() => {
    void load()
  }, [load])

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    void load(search || undefined)
  }

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      const created = await createTeam(newName)
      await refresh()
      navigate(`/teams/${created.id}`)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleJoinRequest = async (teamId: string, teamName: string) => {
    if (!window.confirm(`Send request to join ${teamName}?`)) return
    setError(null)
    setMessage(null)
    try {
      await requestToJoin(teamId)
      setMessage('Join request sent — the team leader has been notified.')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const canJoin = (team: TeamListItem) =>
    !isAdmin && !myTeam && (team.status === 'open' || team.status === 'looking_for_teammates')

  return (
    <div>
      <h1>Teams</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      {isAdmin && <p className="muted">Viewing as admin — read-only, you can't create or join a team.</p>}

      {!isAdmin && !myTeam && (
        <form className="inline-form" onSubmit={handleCreate}>
          <input
            placeholder="New team name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            required
          />
          <button type="submit">Create team</button>
        </form>
      )}

      <form className="inline-form" onSubmit={handleSearch}>
        <input
          placeholder="Search teams…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>Ref</th>
            <th>Name</th>
            <th>Members</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {teams.map((team) => (
            <tr key={team.id}>
              <td>{team.reference_id ?? '—'}</td>
              <td>
                <Link to={`/teams/${team.id}`}>{team.name}</Link>
              </td>
              <td>
                {team.member_count}/{team.capacity}
              </td>
              <td>
                <span className={`badge status-${team.status}`}>{team.status}</span>
              </td>
              <td>
                {canJoin(team) && (
                  <button onClick={() => void handleJoinRequest(team.id, team.name)}>
                    Request to join
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {teams.length === 0 && <p>No teams found.</p>}
    </div>
  )
}
