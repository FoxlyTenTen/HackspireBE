import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { getParticipants, getTeam, listTeams } from '../api/endpoints'
import type { TeamRead } from '../api/types'
import { useAuth } from './AuthContext'

interface MyTeamValue {
  /** Full detail of the viewer's team, or null when they have no team. */
  team: TeamRead | null
  isLeader: boolean
  loading: boolean
  /** Re-derive after any action that changes team membership. */
  refresh: () => Promise<void>
}

const MyTeamContext = createContext<MyTeamValue | null>(null)

/**
 * There is no /me endpoint, so the viewer's team is derived from the
 * participant list (self row carries team_name) matched against the team list.
 */
export function MyTeamProvider({ children }: { children: ReactNode }) {
  const { auth } = useAuth()
  const userId = auth?.userId ?? ''
  const [team, setTeam] = useState<TeamRead | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const participants = await getParticipants()
      const me = participants.find((p) => p.id === userId)
      if (!me || me.status === 'no_team' || !me.team_name) {
        setTeam(null)
        return
      }
      const teams = await listTeams(me.team_name)
      const mine = teams.find((t) => t.name === me.team_name)
      setTeam(mine ? await getTeam(mine.id) : null)
    } catch {
      setTeam(null)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const isLeader = team !== null && team.leader_id === userId

  return (
    <MyTeamContext.Provider value={{ team, isLeader, loading, refresh }}>
      {children}
    </MyTeamContext.Provider>
  )
}

export function useMyTeam(): MyTeamValue {
  const value = useContext(MyTeamContext)
  if (!value) throw new Error('useMyTeam must be used inside MyTeamProvider')
  return value
}
