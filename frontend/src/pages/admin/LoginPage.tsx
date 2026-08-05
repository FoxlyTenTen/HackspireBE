import { Navigate, useNavigate } from 'react-router-dom'
import LoginForm from '../../components/LoginForm'
import { useAuth } from '../../context/AuthContext'

export default function AdminLoginPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()

  if (auth && auth.role === 'admin' && !auth.firstLogin) {
    return <Navigate to="/administrator/teams" replace />
  }

  return (
    <LoginForm
      expectedRole="admin"
      title="Administrator Login"
      onSuccess={(firstLogin) =>
        navigate(firstLogin ? '/change-password' : '/administrator/teams', { replace: true })
      }
    />
  )
}
