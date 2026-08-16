import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { getProfile, updateProfile } from '../../api/endpoints'
import type { ProfileRead } from '../../api/types'
import ErrorBanner from '../../components/ErrorBanner'
import { formatDateTime } from '../../utils'

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileRead | null>(null)
  const [username, setUsername] = useState('')
  const [universityName, setUniversityName] = useState('')
  const [technicalSkills, setTechnicalSkills] = useState('')
  const [preferredRole, setPreferredRole] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const load = () =>
    getProfile()
      .then((p) => {
        setProfile(p)
        setUsername(p.username ?? '')
        setUniversityName(p.university_name ?? '')
        setTechnicalSkills(p.technical_skills ?? '')
        setPreferredRole(p.preferred_role ?? '')
      })
      .catch((err: Error) => setError(err.message))

  useEffect(() => {
    void load()
  }, [])

  if (!profile) return error ? <ErrorBanner message={error} /> : <p>Loading…</p>

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      const updated = await updateProfile({
        username: username || null,
        university_name: universityName || null,
        technical_skills: technicalSkills || null,
        preferred_role: preferredRole || null,
      })
      setProfile(updated)
      setMessage('Profile updated.')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <h1>My Profile</h1>
      <ErrorBanner message={error} />
      {message && <div className="success-banner">{message}</div>}

      <p>
        <strong>Name:</strong> {profile.name}
        <br />
        <strong>Email:</strong> {profile.email}{' '}
        <span className="muted">(contact an admin to correct this)</span>
        <br />
        <strong>Student/Staff ID:</strong> {profile.student_staff_id}
        {profile.reference_id && (
          <>
            <br />
            <strong>Reference ID:</strong> {profile.reference_id}
          </>
        )}
        <br />
        <strong>Joined:</strong> {formatDateTime(profile.created_at)}
      </p>

      <form className="stack-form" onSubmit={handleSubmit}>
        <label>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Pick a unique username"
          />
        </label>
        <label>
          University name
          <input
            value={universityName}
            onChange={(e) => setUniversityName(e.target.value)}
            placeholder="e.g. Universiti Malaya"
          />
        </label>
        <label>
          Technical skills
          <input
            value={technicalSkills}
            onChange={(e) => setTechnicalSkills(e.target.value)}
            placeholder="e.g. React, Python, Figma"
          />
        </label>
        <label>
          Preferred role
          <input
            value={preferredRole}
            onChange={(e) => setPreferredRole(e.target.value)}
            placeholder="e.g. Frontend, Design, Pitching"
          />
        </label>
        <button type="submit">Save profile</button>
      </form>
    </div>
  )
}
