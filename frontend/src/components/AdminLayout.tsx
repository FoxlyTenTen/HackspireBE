import { Outlet } from 'react-router-dom'
import {
  AnnouncementsIcon,
  AuditLogIcon,
  BootcampsIcon,
  EventContentIcon,
  HomeIcon,
  MaterialsIcon,
  ParticipantsIcon,
  ResultsIcon,
  SubmissionIcon,
  TeamsIcon,
} from './icons'
import Sidebar from './Sidebar'
import type { SidebarItem } from './Sidebar'
import TopBar from './TopBar'

const items: SidebarItem[] = [
  { to: '/administrator/participants', label: 'Participants', icon: <ParticipantsIcon /> },
  { to: '/administrator/teams', label: 'Teams', icon: <TeamsIcon /> },
  { to: '/administrator/event', label: 'Events', icon: <EventContentIcon /> },
  { to: '/administrator/bootcamps', label: 'Bootcamps', icon: <BootcampsIcon /> },
  { to: '/administrator/announcements', label: 'Announcements', icon: <AnnouncementsIcon /> },
  { to: '/administrator/materials', label: 'Materials', icon: <MaterialsIcon /> },
  { to: '/administrator/results', label: 'Results', icon: <ResultsIcon /> },
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
