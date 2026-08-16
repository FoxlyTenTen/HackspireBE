import { Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { MyTeamProvider, useMyTeam } from '../context/MyTeamContext'
import {
  AnnouncementsIcon,
  BackIcon,
  HomeIcon,
  MyTeamIcon,
  ParticipantsIcon,
  SubmissionIcon,
  TeamsIcon,
} from './icons'
import Sidebar from './Sidebar'
import type { SidebarItem } from './Sidebar'
import TopBar from './TopBar'

function Shell() {
  const { auth } = useAuth()
  const isAdmin = auth?.role === 'admin'
  const { team } = useMyTeam()

  const items: SidebarItem[] = [
    { to: '/', label: 'Home', icon: <HomeIcon />, end: true },
    { to: '/teams', label: 'Teams', icon: <TeamsIcon /> },
    { to: '/participants', label: 'Participants', icon: <ParticipantsIcon /> },
    { to: '/announcements', label: 'Announcements', icon: <AnnouncementsIcon /> },
  ]
  if (team) {
    items.push({ to: `/teams/${team.id}`, label: 'My Team', icon: <MyTeamIcon /> })
    items.push({
      to: `/teams/${team.id}/submission`,
      label: 'Submission',
      icon: <SubmissionIcon />,
    })
  }
  if (isAdmin) {
    items.push({ to: '/administrator/teams', label: 'Back to Admin', icon: <BackIcon /> })
  }

  return (
    <div className="app-shell">
      <Sidebar
        brand="HACKSPIRE: LUMINA"
        items={items}
        storageKey="sidebar-collapsed-participant"
      />
      <div className="app-main">
        <TopBar
          previewBadge={isAdmin}
          showProfile={!isAdmin}
          showNotifications
          logoutRedirect={isAdmin ? '/administrator' : '/login'}
        />
        <main className="container">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default function ParticipantLayout() {
  return (
    <MyTeamProvider>
      <Shell />
    </MyTeamProvider>
  )
}
