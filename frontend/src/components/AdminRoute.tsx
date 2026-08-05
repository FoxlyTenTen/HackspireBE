import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/** Admin guard — independent from the participant ProtectedRoute. */
export default function AdminRoute() {
  const { auth } = useAuth()
  if (!auth) return <Navigate to="/administrator" replace />
  if (auth.role !== 'admin') return <Navigate to="/login" replace />
  if (auth.firstLogin) return <Navigate to="/change-password" replace />
  return <Outlet />
}
