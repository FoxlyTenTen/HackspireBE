import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { MyTeamProvider, useMyTeam } from '../context/MyTeamContext'

function NavBar() {
  const { auth, logout } = useAuth()
  const isAdmin = auth?.role === 'admin'
  const { team } = useMyTeam()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate(isAdmin ? '/administrator' : '/login')
  }

  return (
    <nav className="navbar">
      <Link to="/" className="brand">
        HACKSPIRE: LUMINA {isAdmin && <span className="badge">admin view</span>}
      </Link>
      <NavLink to="/">Home</NavLink>
      <NavLink to="/teams">Teams</NavLink>
      <NavLink to="/participants">Participants</NavLink>
      <NavLink to="/announcements">Announcements</NavLink>
      <NavLink to="/notifications">Notifications</NavLink>
      {team && <NavLink to={`/teams/${team.id}`}>My Team</NavLink>}
      {team && <NavLink to={`/teams/${team.id}/submission`}>Submission</NavLink>}
      {!isAdmin && <NavLink to="/profile">Profile</NavLink>}
      {isAdmin && (
        <Link to="/administrator/teams">Back to Admin</Link>
      )}
      <button className="link-button" onClick={handleLogout}>
        Log out
      </button>
    </nav>
  )
}

export default function ParticipantLayout() {
  return (
    <MyTeamProvider>
      <NavBar />
      <main className="container">
        <Outlet />
      </main>
    </MyTeamProvider>
  )
}
