import { Navigate, useNavigate } from 'react-router-dom'
import LoginForm from '../../components/LoginForm'
import { useAuth } from '../../context/AuthContext'

export default function LoginPage() {
  const { auth } = useAuth()
  const navigate = useNavigate()

  if (auth && auth.role === 'participant' && !auth.firstLogin) {
    return <Navigate to="/" replace />
  }

  return (
    <LoginForm
      expectedRole="participant"
      title="Participant Login"
      onSuccess={(firstLogin) => navigate(firstLogin ? '/change-password' : '/', { replace: true })}
    />
  )
}
