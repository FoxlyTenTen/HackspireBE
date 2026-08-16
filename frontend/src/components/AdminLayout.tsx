import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AdminLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/administrator')
  }

  return (
    <>
      <nav className="navbar admin">
        <Link to="/administrator/teams" className="brand">
          LUMINA Admin
        </Link>
        <NavLink to="/administrator/participants">Participants</NavLink>
        <NavLink to="/administrator/teams">Teams</NavLink>
        <NavLink to="/administrator/event">Event Content</NavLink>
        <NavLink to="/administrator/submissions">Submissions</NavLink>
        <NavLink to="/administrator/audit-log">Audit Log</NavLink>
        <Link to="/">View Participant Portal</Link>
        <button className="link-button" onClick={handleLogout}>
          Log out
        </button>
      </nav>
      <main className="container">
        <Outlet />
      </main>
    </>
  )
}
