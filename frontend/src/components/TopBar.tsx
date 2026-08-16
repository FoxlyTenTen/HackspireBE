import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ProfileIcon } from './icons'
import NotificationBell from './NotificationBell'

interface TopBarProps {
  previewBadge?: boolean
  showProfile?: boolean
  showNotifications?: boolean
  logoutRedirect: string
  variant?: 'admin'
}

export default function TopBar({
  previewBadge,
  showProfile = true,
  showNotifications = true,
  logoutRedirect,
  variant,
}: TopBarProps) {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate(logoutRedirect)
  }

  return (
    <header className={`app-topbar${variant ? ` ${variant}` : ''}`}>
      {previewBadge && <span className="badge">admin view</span>}
      <div className="topbar-actions">
        {showNotifications && <NotificationBell />}
        {showProfile && (
          <Link to="/profile" className="topbar-icon-link" title="Profile" aria-label="Profile">
            <ProfileIcon />
          </Link>
        )}
        <button className="link-button" onClick={handleLogout}>
          Log out
        </button>
      </div>
    </header>
  )
}
