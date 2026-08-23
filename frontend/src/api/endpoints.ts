import axios from 'axios'
import client from './client'
import type {
  AdminParticipantsResponse,
  AdminSubmissionRow,
  AdminTeamRead,
  AdminTeamUpdate,
  AnnouncementRead,
  AuditLogRead,
  EventInfo,
  EventSettingsRead,
  FinalistRead,
  ImportConfirmResponse,
  ImportPreviewResponse,
  JoinRequestRead,
  LoginResponse,
  MaterialCategory,
  MaterialRead,
  NotificationRead,
  ParticipantListItem,
  ProfileRead,
  ProfileUpdate,
  ResetPasswordResponse,
  SubmissionRead,
  TeamListItem,
  TeamRead,
  TeamStatus,
  TimelineImportConfirmResponse,
  TimelineImportPreviewResponse,
  TimelineItem,
  TimelineItemWrite,
  WinnerRead,
} from './types'

// ---------- Auth ----------
export const login = (username: string, password: string) =>
  client.post<LoginResponse>('/auth/login', { username, password }).then((r) => r.data)

export const changePassword = (new_password: string) =>
  client.post('/auth/change-password', { new_password }).then((r) => r.data)

/** Self-service reset — Supabase sends its built-in reset email. */
export const forgotPassword = (email: string) =>
  client.post<{ message: string }>('/auth/forgot-password', { email }).then((r) => r.data)

/** Exchanges a PKCE-flow email link's `token_hash` for a real session. */
export const verifyOtp = (tokenHash: string, type: string) =>
  axios
    .post<{ jwt: string; refresh_token: string; type: string }>(
      `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/auth/verify-otp`,
      { token_hash: tokenHash, type },
    )
    .then((r) => r.data)
    .catch((err) => {
      throw new Error(err.response?.data?.error ?? err.message ?? 'Request failed')
    })

/**
 * Set a password using a token from an invite / recovery link's URL fragment
 * (the user has no stored session yet, so the token is passed explicitly).
 */
export const setPasswordWithToken = (accessToken: string, new_password: string) =>
  axios
    .post(
      `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/auth/change-password`,
      { new_password },
      { headers: { Authorization: `Bearer ${accessToken}` } },
    )
    .then((r) => r.data)
    .catch((err) => {
      throw new Error(err.response?.data?.error ?? err.message ?? 'Request failed')
    })

// ---------- Profile ----------
// No self-service email change — participants ask an admin to correct it
// (adminChangeParticipantEmail below), which updates Supabase Auth directly.
export const getProfile = () => client.get<ProfileRead>('/profile').then((r) => r.data)

export const updateProfile = (body: ProfileUpdate) =>
  client.patch<ProfileRead>('/profile', body).then((r) => r.data)

// ---------- Home / Content ----------
export const getEventInfo = () =>
  client.get<EventInfo>('/event/info').then((r) => r.data)

export const getMaterials = () =>
  client.get<MaterialRead[]>('/materials').then((r) => r.data)

export const downloadMaterial = (materialId: string) =>
  client
    .get<Blob>(`/materials/${materialId}/download`, { responseType: 'blob' })
    .then((r) => r.data)

export const getFinalists = () =>
  client.get<FinalistRead[]>('/finalists').then((r) => r.data)

export const getWinners = () =>
  client.get<WinnerRead[]>('/winners').then((r) => r.data)

export const getAnnouncements = () =>
  client.get<AnnouncementRead[]>('/announcements').then((r) => r.data)

export const getAnnouncement = (announcementId: string) =>
  client.get<AnnouncementRead>(`/announcements/${announcementId}`).then((r) => r.data)

// ---------- Participants ----------
export const getParticipants = (search?: string) =>
  client
    .get<ParticipantListItem[]>('/participants', { params: search ? { search } : {} })
    .then((r) => r.data)

// ---------- Teams ----------
export const listTeams = (search?: string) =>
  client
    .get<TeamListItem[]>('/teams', { params: search ? { search } : {} })
    .then((r) => r.data)

export const createTeam = (name: string) =>
  client.post<TeamRead>('/teams', { name }).then((r) => r.data)

export const getTeam = (teamId: string) =>
  client.get<TeamRead>(`/teams/${teamId}`).then((r) => r.data)

export const updateTeam = (
  teamId: string,
  body: { name?: string; capacity?: number; status?: TeamStatus },
) => client.patch<TeamRead>(`/teams/${teamId}`, body).then((r) => r.data)

export const deleteTeam = (teamId: string) =>
  client.delete(`/teams/${teamId}`).then((r) => r.data)

export const inviteParticipant = (teamId: string, participant_id: string) =>
  client.post<JoinRequestRead>(`/teams/${teamId}/invite`, { participant_id }).then((r) => r.data)

export const removeTeamMember = (teamId: string, participantId: string) =>
  client.delete(`/teams/${teamId}/members/${participantId}`).then((r) => r.data)

export const leaveTeam = (teamId: string) =>
  client.post(`/teams/${teamId}/leave`).then((r) => r.data)

export const requestToJoin = (teamId: string) =>
  client.post<JoinRequestRead>(`/teams/${teamId}/join-requests`).then((r) => r.data)

// ---------- Join Requests ----------
export const getJoinRequests = () =>
  client.get<JoinRequestRead[]>('/join-requests').then((r) => r.data)

export const getInvitations = () =>
  client.get<JoinRequestRead[]>('/join-requests/invitations').then((r) => r.data)

export const respondToJoinRequest = (requestId: string, decision: 'approve' | 'reject') =>
  client
    .post<JoinRequestRead>(`/join-requests/${requestId}/respond`, { decision })
    .then((r) => r.data)

// ---------- Notifications ----------
export const getNotifications = () =>
  client.get<NotificationRead[]>('/notifications').then((r) => r.data)

export const markNotificationRead = (notificationId: string) =>
  client
    .patch<NotificationRead>(`/notifications/${notificationId}/read`)
    .then((r) => r.data)

// ---------- Submission ----------
export const getSubmission = (teamId: string, round: 1 | 2) =>
  client.get<SubmissionRead>(`/teams/${teamId}/submission/${round}`).then((r) => r.data)

export const createSubmission = (
  teamId: string,
  round: 1 | 2,
  body: {
    github_url?: string | null
    infographic_url?: string | null
    pitch_deck_url?: string | null
  },
) => client.post<SubmissionRead>(`/teams/${teamId}/submission/${round}`, body).then((r) => r.data)

export const updateSubmission = (
  teamId: string,
  round: 1 | 2,
  body: {
    github_url?: string | null
    infographic_url?: string | null
    pitch_deck_url?: string | null
  },
) => client.patch<SubmissionRead>(`/teams/${teamId}/submission/${round}`, body).then((r) => r.data)

// ---------- Admin — Participants ----------
export const adminImportPreview = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return client
    .post<ImportPreviewResponse>('/admin/participants/import', form)
    .then((r) => r.data)
}

export const adminImportConfirm = (
  rows: {
    name: string
    email: string
    student_staff_id: string
    reference_id?: string | null
    university_name?: string | null
    technical_skills?: string | null
    preferred_role?: string | null
  }[],
) =>
  client
    .post<ImportConfirmResponse>('/admin/participants/import/confirm', { rows })
    .then((r) => r.data)

export const adminGetParticipants = () =>
  client.get<AdminParticipantsResponse>('/admin/participants').then((r) => r.data)

export const adminParticipantsCsv = () =>
  client
    .get<Blob>('/admin/participants', { params: { format: 'csv' }, responseType: 'blob' })
    .then((r) => r.data)

export const adminResetPassword = (participantId: string) =>
  client
    .post<ResetPasswordResponse>(`/admin/participants/${participantId}/reset-password`)
    .then((r) => r.data)

/** Correct a wrongly-imported email; re-sends the set-password link if the account was never activated. */
export const adminChangeParticipantEmail = (participantId: string, new_email: string) =>
  client
    .post<{ message: string }>(`/admin/participants/${participantId}/change-email`, { new_email })
    .then((r) => r.data)

// ---------- Admin — Teams ----------
export const adminGetTeams = () =>
  client.get<AdminTeamRead[]>('/admin/teams').then((r) => r.data)

export const adminApproveTeam = (teamId: string) =>
  client.post<AdminTeamRead>(`/admin/teams/${teamId}/approve`).then((r) => r.data)

export const adminRejectTeam = (teamId: string, note?: string) =>
  client
    .post<AdminTeamRead>(`/admin/teams/${teamId}/reject`, note ? { note } : {})
    .then((r) => r.data)

export const adminUpdateTeam = (teamId: string, body: AdminTeamUpdate) =>
  client.patch<AdminTeamRead>(`/admin/teams/${teamId}`, body).then((r) => r.data)

export const adminDeleteTeam = (teamId: string) =>
  client.delete(`/admin/teams/${teamId}`).then((r) => r.data)

// ---------- Admin — Event Content ----------
export const adminSetCountdown = (countdown_at: string) =>
  client
    .patch<EventSettingsRead>('/admin/event/countdown', { countdown_at })
    .then((r) => r.data)

export const adminSetTimeline = (items: TimelineItemWrite[]) =>
  client.patch<TimelineItem[]>('/admin/event/timeline', { items }).then((r) => r.data)

export const adminUpdateTimelineItem = (
  itemId: string,
  fields: {
    bootcamp_name?: string
    date_label?: string
    time_session?: string
    session_type?: string
    speaker_name?: string
    speaker_bio?: string
    organization?: string
    session_description?: string
    speaker_photo_url?: string
    status?: string
    remarks?: string
    order_index?: number
    zoom_link?: string
  },
  material?: File | null,
  removeMaterial?: boolean,
) => {
  const form = new FormData()
  for (const [key, value] of Object.entries(fields)) {
    if (value !== undefined) form.append(key, String(value))
  }
  if (material) form.append('material', material)
  if (removeMaterial) form.append('remove_material', 'true')
  return client
    .patch<TimelineItem>(`/admin/event/timeline/${itemId}`, form)
    .then((r) => r.data)
}

export const adminTimelineImportPreview = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return client
    .post<TimelineImportPreviewResponse>('/admin/timeline/import', form)
    .then((r) => r.data)
}

export const adminTimelineImportConfirm = (rows: TimelineItemWrite[]) =>
  client
    .post<TimelineImportConfirmResponse>('/admin/timeline/import/confirm', { rows })
    .then((r) => r.data)

export const adminPutFinalists = (team_ids: string[], published: boolean) =>
  client.put<FinalistRead[]>('/admin/finalists', { team_ids, published }).then((r) => r.data)

export const adminPutWinners = (
  winners: { team_id: string; placement: string }[],
  published: boolean,
) => client.put<WinnerRead[]>('/admin/winners', { winners, published }).then((r) => r.data)

export const adminUploadMaterial = (file: File, category: MaterialCategory = 'general') => {
  const form = new FormData()
  form.append('file', file)
  form.append('category', category)
  return client.post<MaterialRead>('/admin/materials', form).then((r) => r.data)
}

export const adminDeleteMaterial = (materialId: string) =>
  client.delete(`/admin/materials/${materialId}`).then((r) => r.data)

export const adminPostAnnouncement = (title: string, body: string, image?: File | null) => {
  const form = new FormData()
  form.append('title', title)
  form.append('body', body)
  if (image) form.append('image', image)
  return client.post<AnnouncementRead>('/admin/announcements', form).then((r) => r.data)
}

export const adminUpdateAnnouncement = (
  announcementId: string,
  fields: { title?: string; body?: string; image?: File | null },
) => {
  const form = new FormData()
  if (fields.title !== undefined) form.append('title', fields.title)
  if (fields.body !== undefined) form.append('body', fields.body)
  if (fields.image) form.append('image', fields.image)
  return client
    .patch<AnnouncementRead>(`/admin/announcements/${announcementId}`, form)
    .then((r) => r.data)
}

export const adminDeleteAnnouncement = (announcementId: string) =>
  client.delete(`/admin/announcements/${announcementId}`).then((r) => r.data)

export const adminGetAuditLog = (limit = 100, offset = 0) =>
  client
    .get<AuditLogRead[]>('/admin/audit-log', { params: { limit, offset } })
    .then((r) => r.data)

// ---------- Admin — Submissions ----------
export const adminGetSubmissions = (round?: 1 | 2) =>
  client
    .get<AdminSubmissionRow[]>('/admin/submissions', { params: round ? { round } : {} })
    .then((r) => r.data)

export const adminSubmissionsCsv = (round?: 1 | 2) =>
  client
    .get<Blob>('/admin/submissions', {
      params: { format: 'csv', ...(round ? { round } : {}) },
      responseType: 'blob',
    })
    .then((r) => r.data)

export const adminSetDeadline = (round: 1 | 2, submission_deadline_at: string) =>
  client
    .patch<EventSettingsRead>('/admin/submissions/deadline', { round, submission_deadline_at })
    .then((r) => r.data)
