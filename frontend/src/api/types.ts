export type Role = 'participant' | 'admin'
export type TeamStatus = 'open' | 'looking_for_teammates' | 'closed' | 'full'
export type ApprovalStatus = 'pending' | 'approved' | 'rejected'
export type TimelineStatus = 'TBD' | 'Proposed' | 'Confirmed' | 'Declined'
export type MaterialCategory = 'general' | 'submission_template'

export interface LoginResponse {
  jwt: string
  refresh_token: string
  first_login: boolean
  role: Role
}

export interface RefreshResponse {
  jwt: string
  refresh_token: string
}

export interface ParticipantListItem {
  id: string
  name: string
  username: string | null
  reference_id: string | null
  technical_skills: string | null
  preferred_role: string | null
  status: 'no_team' | 'in_team'
  team_name: string | null
}

export interface TeamListItem {
  id: string
  name: string
  reference_id: string | null
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
  reference_id: string | null
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
  round: 1 | 2
  github_url: string | null
  infographic_url: string | null
  pitch_deck_url: string | null
  submitted_by: string | null
  submitted_at: string
  updated_at: string
}

export interface TimelineItem {
  id: string
  bootcamp_name: string
  date_label: string
  time_session: string
  session_type: string
  speaker_name: string | null
  speaker_bio: string | null
  organization: string | null
  session_description: string | null
  speaker_photo_url: string | null
  status: TimelineStatus
  remarks: string | null
  order_index: number
}

export interface TimelineItemWrite {
  bootcamp_name: string
  date_label: string
  time_session: string
  session_type: string
  speaker_name?: string | null
  speaker_bio?: string | null
  organization?: string | null
  session_description?: string | null
  speaker_photo_url?: string | null
  status: TimelineStatus
  remarks?: string | null
  order_index: number
}

export interface TimelineImportRow {
  row_number: number
  bootcamp_name: string | null
  date_label: string | null
  time_session: string | null
  session_type: string | null
  speaker_name: string | null
  speaker_bio: string | null
  organization: string | null
  session_description: string | null
  speaker_photo_url: string | null
  status: string | null
  remarks: string | null
  order_index: number
  row_status: 'ok' | 'flagged'
  issues: string[]
}

export interface TimelineImportPreviewResponse {
  rows: TimelineImportRow[]
  ok_count: number
  flagged_count: number
}

export interface TimelineImportConfirmResponse {
  created: number
}

export interface EventInfo {
  name: string
  tagline: string
  venue: string
  countdown_at: string | null
  submission_deadline_at: string | null
  round2_submission_deadline_at: string | null
  timeline: TimelineItem[]
  sponsors: { name: string; tier: string }[]
  prize_pool: { total: string; breakdown: { placement: string; prize: string }[] }
  contact: Record<string, string>
}

export interface MaterialRead {
  id: string
  file_name: string
  file_url: string
  category: MaterialCategory
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
  image_url: string | null
  posted_by: string
  posted_at: string
  updated_at: string | null
}

export interface ImportRow {
  row_number: number
  name: string | null
  email: string | null
  student_staff_id: string | null
  reference_id: string | null
  university_name: string | null
  technical_skills: string | null
  preferred_role: string | null
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
  invite_failed: number
  skipped_rows: ImportRow[]
}

export interface ProfileRead {
  id: string
  name: string
  email: string
  student_staff_id: string
  role: Role
  first_login: boolean
  username: string | null
  reference_id: string | null
  university_name: string | null
  technical_skills: string | null
  preferred_role: string | null
  invite_status: 'invited' | 'active' | 'failed' | null
  created_at: string
}

export interface ProfileUpdate {
  username?: string | null
  university_name?: string | null
  technical_skills?: string | null
  preferred_role?: string | null
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
  reference_id: string | null
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
  team_reference_id: string | null
  team_name: string
  round: 1 | 2
  github_url: string | null
  infographic_url: string | null
  pitch_deck_url: string | null
  submitted_at: string
  updated_at: string
}

export interface EventSettingsRead {
  countdown_at: string | null
  submission_deadline_at: string | null
  round2_submission_deadline_at: string | null
  updated_at: string
}

export interface AuditLogRead {
  id: string
  admin_id: string
  admin_name: string | null
  action: string
  target_table: string | null
  target_id: string | null
  details: string | null
  created_at: string
}
