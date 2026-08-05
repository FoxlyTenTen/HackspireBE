export type Role = 'participant' | 'admin'
export type TeamStatus = 'open' | 'looking_for_teammates' | 'closed' | 'full'
export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

export interface LoginResponse {
  jwt: string
  first_login: boolean
  role: Role
}

export interface ParticipantListItem {
  id: string
  name: string
  student_staff_id: string
  status: 'no_team' | 'in_team'
  team_name: string | null
}

export interface TeamListItem {
  id: string
  name: string
  member_count: number
  capacity: number
  status: TeamStatus
}

export interface TeamMemberRead {
  participant_id: string
  name: string
  student_staff_id: string
  is_leader: boolean
  joined_at: string
}

export interface TeamRead {
  id: string
  name: string
  leader_id: string
  capacity: number
  status: TeamStatus
  approval_status: ApprovalStatus
  admin_note: string | null
  locked: boolean
  created_at: string
  member_count: number
  members: TeamMemberRead[]
}

export interface JoinRequestRead {
  id: string
  team_id: string
  team_name: string
  participant_id: string
  participant_name: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  responded_at: string | null
}

export interface NotificationRead {
  id: string
  type: 'join_request' | 'join_response' | 'announcement' | 'team_update'
  reference_id: string | null
  message: string
  read: boolean
  created_at: string
}

export interface SubmissionRead {
  id: string
  team_id: string
  url: string
  submitted_at: string
  updated_at: string
}

export interface TimelineItem {
  id: string
  time_label: string
  title: string
  description: string | null
  order_index: number
}

export interface TimelineItemWrite {
  time_label: string
  title: string
  description?: string | null
  order_index: number
}

export interface EventInfo {
  name: string
  tagline: string
  venue: string
  countdown_at: string | null
  submission_deadline_at: string | null
  timeline: TimelineItem[]
  sponsors: { name: string; tier: string }[]
  prize_pool: { total: string; breakdown: { placement: string; prize: string }[] }
  contact: Record<string, string>
}

export interface MaterialRead {
  id: string
  file_name: string
  file_url: string
  uploaded_at: string
}

export interface FinalistRead {
  id: string
  team_id: string
  team_name: string
  published: boolean
  published_at: string | null
}

export interface WinnerRead {
  id: string
  team_id: string
  team_name: string
  placement: string
  published: boolean
  published_at: string | null
}

export interface AnnouncementRead {
  id: string
  title: string
  body: string
  posted_by: string
  posted_at: string
}

export interface ImportRow {
  row_number: number
  name: string | null
  email: string | null
  student_staff_id: string | null
  status: 'ok' | 'flagged'
  issues: string[]
}

export interface ImportPreviewResponse {
  rows: ImportRow[]
  ok_count: number
  flagged_count: number
}

export interface ImportConfirmResponse {
  created: number
  skipped: number
  skipped_rows: ImportRow[]
}

export interface ProfileRead {
  id: string
  name: string
  email: string
  student_staff_id: string
  role: Role
  first_login: boolean
  created_at: string
}

export interface AdminParticipantsResponse {
  count: number
  cap: number
  remaining: number
  participants: ProfileRead[]
}

export interface ResetPasswordResponse {
  participant_id: string
  temporary_password: string
}

export interface AdminTeamRead {
  id: string
  name: string
  leader_id: string
  leader_name: string
  member_count: number
  capacity: number
  status: TeamStatus
  approval_status: ApprovalStatus
  admin_note: string | null
  locked: boolean
  has_submission: boolean
  created_at: string
}

export interface AdminTeamUpdate {
  name?: string
  capacity?: number
  status?: TeamStatus
  leader_id?: string
  locked?: boolean
}

export interface AdminSubmissionRow {
  team_id: string
  team_name: string
  url: string
  submitted_at: string
  updated_at: string
}

export interface EventSettingsRead {
  countdown_at: string | null
  submission_deadline_at: string | null
  updated_at: string
}
