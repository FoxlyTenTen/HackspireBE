import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './components/AdminLayout'
import AdminRoute from './components/AdminRoute'
import ParticipantLayout from './components/ParticipantLayout'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import AdminLoginPage from './pages/admin/LoginPage'
import AdminParticipantsPage from './pages/admin/ParticipantsPage'
import AdminSubmissionsPage from './pages/admin/SubmissionsPage'
import AdminTeamsPage from './pages/admin/TeamsPage'
import EventContentPage from './pages/admin/EventContentPage'
import AnnouncementsPage from './pages/participant/AnnouncementsPage'
import ChangePasswordPage from './pages/participant/ChangePasswordPage'
import HomePage from './pages/participant/HomePage'
import LoginPage from './pages/participant/LoginPage'
import NotificationsPage from './pages/participant/NotificationsPage'
import ParticipantsPage from './pages/participant/ParticipantsPage'
import ProfilePage from './pages/participant/ProfilePage'
import SubmissionPage from './pages/participant/SubmissionPage'
import TeamsPage from './pages/participant/TeamsPage'
import YourTeamPage from './pages/participant/YourTeamPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public entry points — two independent login pages */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/administrator" element={<AdminLoginPage />} />
          <Route path="/change-password" element={<ChangePasswordPage />} />

          {/* Participant tree */}
          <Route element={<ProtectedRoute />}>
            <Route element={<ParticipantLayout />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/participants" element={<ParticipantsPage />} />
              <Route path="/teams" element={<TeamsPage />} />
              <Route path="/teams/:teamId" element={<YourTeamPage />} />
              <Route path="/teams/:teamId/submission" element={<SubmissionPage />} />
              <Route path="/notifications" element={<NotificationsPage />} />
              <Route path="/announcements" element={<AnnouncementsPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
          </Route>

          {/* Admin tree — separate guard */}
          <Route element={<AdminRoute />}>
            <Route element={<AdminLayout />}>
              <Route path="/administrator/participants" element={<AdminParticipantsPage />} />
              <Route path="/administrator/teams" element={<AdminTeamsPage />} />
              <Route path="/administrator/event" element={<EventContentPage />} />
              <Route path="/administrator/submissions" element={<AdminSubmissionsPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
