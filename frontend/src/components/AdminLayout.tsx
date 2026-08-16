import { Outlet } from 'react-router-dom'
import {
  AuditLogIcon,
  EventContentIcon,
  HomeIcon,
  ParticipantsIcon,
  SubmissionIcon,
  TeamsIcon,
} from './icons'
import Sidebar from './Sidebar'
import type { SidebarItem } from './Sidebar'
import TopBar from './TopBar'

const items: SidebarItem[] = [
  { to: '/administrator/participants', label: 'Participants', icon: <ParticipantsIcon /> },
  { to: '/administrator/teams', label: 'Teams', icon: <TeamsIcon /> },
  { to: '/administrator/event', label: 'Event Content', icon: <EventContentIcon /> },
  { to: '/administrator/submissions', label: 'Submissions', icon: <SubmissionIcon /> },
  { to: '/administrator/audit-log', label: 'Audit Log', icon: <AuditLogIcon /> },
  { to: '/', label: 'View Participant Portal', icon: <HomeIcon /> },
]

export default function AdminLayout() {
  return (
    <div className="app-shell">
      <Sidebar
        brand="LUMINA Admin"
        items={items}
        storageKey="sidebar-collapsed-admin"
        variant="admin"
      />
      <div className="app-main">
        <TopBar showProfile={false} showNotifications={false} logoutRedirect="/administrator" />
        <main className="container">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
