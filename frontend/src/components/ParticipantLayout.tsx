import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { MyTeamProvider, useMyTeam } from '../context/MyTeamContext'

function NavBar() {
  const { logout } = useAuth()
  const { team } = useMyTeam()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <Link to="/" className="brand">
        HACKSPIRE: LUMINA
      </Link>
      <NavLink to="/">Home</NavLink>
      <NavLink to="/teams">Teams</NavLink>
      <NavLink to="/participants">Participants</NavLink>
      <NavLink to="/notifications">Notifications</NavLink>
      {team && <NavLink to={`/teams/${team.id}`}>My Team</NavLink>}
      {team && <NavLink to={`/teams/${team.id}/submission`}>Submission</NavLink>}
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
