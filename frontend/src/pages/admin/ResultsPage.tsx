import { useCallback, useEffect, useState } from 'react'
import { adminGetTeams, adminPutFinalists, adminPutWinners, getFinalists, getWinners } from '../../api/endpoints'
import type { AdminTeamRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { useAdminAction } from '../../hooks/useAdminAction'

export default function ResultsPage() {
  const [teams, setTeams] = useState<AdminTeamRead[]>([])
  const [finalistIds, setFinalistIds] = useState<string[]>([])
  const [finalistsPublished, setFinalistsPublished] = useState(false)
  const [winnerRows, setWinnerRows] = useState<{ team_id: string; placement: string }[]>([])
  const [winnersPublished, setWinnersPublished] = useState(false)
  const { error, message, act } = useAdminAction()

  const load = useCallback(async () => {
    const [teamList, finalists, winners] = await Promise.all([
      adminGetTeams(),
      getFinalists(),
      getWinners(),
    ])
    setTeams(teamList)
    setFinalistIds(finalists.map((f) => f.team_id))
    setFinalistsPublished(finalists.some((f) => f.published))
    setWinnerRows(winners.map((w) => ({ team_id: w.team_id, placement: w.placement })))
    setWinnersPublished(winners.some((w) => w.published))
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div>
      <h1>Results</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      <section>
        <h2>Finalists</h2>
        <p className="muted">Select teams, then publish to make them visible to participants.</p>
        {teams.map((team) => (
          <label key={team.id} className="checkbox">
            <input
              type="checkbox"
              checked={finalistIds.includes(team.id)}
              onChange={(e) =>
                setFinalistIds(
                  e.target.checked
                    ? [...finalistIds, team.id]
                    : finalistIds.filter((id) => id !== team.id),
                )
              }
            />
            {team.name}
          </label>
        ))}
        <label className="checkbox">
          <input
            type="checkbox"
            checked={finalistsPublished}
            onChange={(e) => setFinalistsPublished(e.target.checked)}
          />
          Published (visible to participants)
        </label>
        <button
          type="button"
          onClick={() =>
            void act(
              () => adminPutFinalists(finalistIds, finalistsPublished),
              'Finalist list saved.',
              load,
            )
          }
        >
          Save finalists
        </button>
      </section>

      <section>
        <h2>Winners</h2>
        {winnerRows.map((row, index) => (
          <div className="timeline-row" key={index}>
            <select
              value={row.team_id}
              onChange={(e) => {
                const next = [...winnerRows]
                next[index] = { ...row, team_id: e.target.value }
                setWinnerRows(next)
              }}
            >
              <option value="">— pick a team —</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
            <input
              placeholder="Placement (e.g. champion)"
              value={row.placement}
              onChange={(e) => {
                const next = [...winnerRows]
                next[index] = { ...row, placement: e.target.value }
                setWinnerRows(next)
              }}
            />
            <button
              type="button"
              className="danger"
              onClick={() => setWinnerRows(winnerRows.filter((_, i) => i !== index))}
            >
              ✕
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() => setWinnerRows([...winnerRows, { team_id: '', placement: '' }])}
        >
          + Add winner
        </button>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={winnersPublished}
            onChange={(e) => setWinnersPublished(e.target.checked)}
          />
          Published (visible to participants)
        </label>
        <button
          type="button"
          onClick={() =>
            void act(
              () =>
                adminPutWinners(
                  winnerRows.filter((row) => row.team_id && row.placement),
                  winnersPublished,
                ),
              'Winner list saved.',
              load,
            )
          }
        >
          Save winners
        </button>
      </section>
    </div>
  )
}
