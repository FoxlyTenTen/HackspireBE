import { createContext, useCallback, useContext } from 'react'
import type { ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getParticipants, getTeam, listTeams } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
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
 * The participant list is fetched under the shared `queryKeys.participants('')`
 * key, so this reuses ParticipantsPage's cache instead of a second round trip.
 */
export function MyTeamProvider({ children }: { children: ReactNode }) {
  const { auth } = useAuth()
  const userId = auth?.userId ?? ''
  const queryClient = useQueryClient()

  const { data: team = null, isLoading: loading } = useQuery({
    queryKey: ['my-team', userId],
    enabled: userId !== '',
    queryFn: async (): Promise<TeamRead | null> => {
      const participants = await queryClient.fetchQuery({
        queryKey: queryKeys.participants(),
        queryFn: () => getParticipants(),
      })
      const me = participants.find((p) => p.id === userId)
      if (!me || me.status === 'no_team' || !me.team_name) return null
      const teams = await listTeams(me.team_name)
      const mine = teams.find((t) => t.name === me.team_name)
      return mine ? await getTeam(mine.id) : null
    },
  })

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.participants() })
    await queryClient.invalidateQueries({ queryKey: ['my-team', userId] })
  }, [queryClient, userId])

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
