/** Small inline stroke icons — no icon library dependency in this project. */

const base = {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export function HomeIcon() {
  return (
    <svg {...base}>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5.5 10v9a1 1 0 0 0 1 1H9a1 1 0 0 0 1-1v-4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4a1 1 0 0 0 1 1h2.5a1 1 0 0 0 1-1v-9" />
    </svg>
  )
}

export function TeamsIcon() {
  return (
    <svg {...base}>
      <circle cx="8.5" cy="8" r="3" />
      <path d="M2.5 20a6 6 0 0 1 12 0" />
      <circle cx="17" cy="8.5" r="2.5" />
      <path d="M15.5 13.2A5 5 0 0 1 21.5 18" />
    </svg>
  )
}

export function ParticipantsIcon() {
  return (
    <svg {...base}>
      <circle cx="12" cy="7.5" r="3.5" />
      <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
    </svg>
  )
}

export function AnnouncementsIcon() {
  return (
    <svg {...base}>
      <path d="M3 10v4a1 1 0 0 0 1 1h2l3.5 5V4L6 9H4a1 1 0 0 0-1 1Z" />
      <path d="M14 8.5a4 4 0 0 1 0 7" />
      <path d="M17 5.5a8 8 0 0 1 0 13" />
    </svg>
  )
}

export function MyTeamIcon() {
  return (
    <svg {...base}>
      <path d="M12 3 4 6.5v5c0 5 3.5 8 8 9.5 4.5-1.5 8-4.5 8-9.5v-5Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}

export function SubmissionIcon() {
  return (
    <svg {...base}>
      <path d="M12 16V4" />
      <path d="m7 8.5 5-4.5 5 4.5" />
      <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
    </svg>
  )
}

export function EventContentIcon() {
  return (
    <svg {...base}>
      <rect x="3.5" y="5" width="17" height="15.5" rx="2" />
      <path d="M3.5 9.5h17" />
      <path d="M8 3v3.5M16 3v3.5" />
    </svg>
  )
}

export function AuditLogIcon() {
  return (
    <svg {...base}>
      <path d="M6 3.5h9l4 4V20a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" />
      <path d="M15 3.5V8h4" />
      <path d="M8 12.5h8M8 16h5.5" />
    </svg>
  )
}

export function ProfileIcon() {
  return (
    <svg {...base}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="9.5" r="3" />
      <path d="M6.3 18.5a6.5 6.5 0 0 1 11.4 0" />
    </svg>
  )
}

export function BackIcon() {
  return (
    <svg {...base}>
      <path d="M11 5 4 12l7 7" />
      <path d="M4 12h16" />
    </svg>
  )
}

export function BellIcon() {
  return (
    <svg {...base}>
      <path d="M6 10a6 6 0 0 1 12 0c0 4 1.5 5.5 2 6.5H4c.5-1 2-2.5 2-6.5Z" />
      <path d="M10 19.5a2 2 0 0 0 4 0" />
    </svg>
  )
}
