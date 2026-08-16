import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Participant guard — kept separate from AdminRoute on purpose: the two
 * route trees must be enforced independently. Admins are also let through
 * (read-only browsing of the participant portal) so they can see what
 * participants see without being a real participant — they never appear in
 * the participants list, so nobody can add them to a team.
 */
export default function ProtectedRoute() {
  const { auth } = useAuth()
  if (!auth) return <Navigate to="/login" replace />
  if (auth.role !== 'participant' && auth.role !== 'admin') {
    return <Navigate to="/administrator" replace />
  }
  if (auth.firstLogin) return <Navigate to="/change-password" replace />
  return <Outlet />
}
