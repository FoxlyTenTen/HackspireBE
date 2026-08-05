import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Participant guard — kept separate from AdminRoute on purpose: the two
 * route trees must be enforced independently.
 */
export default function ProtectedRoute() {
  const { auth } = useAuth()
  if (!auth) return <Navigate to="/login" replace />
  if (auth.role !== 'participant') return <Navigate to="/administrator" replace />
  if (auth.firstLogin) return <Navigate to="/change-password" replace />
  return <Outlet />
}
