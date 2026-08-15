import client from './client'
import type {
  AdminParticipantsResponse,
  AdminSubmissionRow,
  AdminTeamRead,
  AdminTeamUpdate,
  AnnouncementRead,
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

// ---------- Profile ----------
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

export const addTeamMember = (teamId: string, participant_id: string) =>
  client.post<TeamRead>(`/teams/${teamId}/members`, { participant_id }).then((r) => r.data)

export const removeTeamMember = (teamId: string, participantId: string) =>
  client.delete(`/teams/${teamId}/members/${participantId}`).then((r) => r.data)

export const leaveTeam = (teamId: string) =>
  client.post(`/teams/${teamId}/leave`).then((r) => r.data)

export const requestToJoin = (teamId: string) =>
  client.post<JoinRequestRead>(`/teams/${teamId}/join-requests`).then((r) => r.data)

// ---------- Join Requests ----------
export const getJoinRequests = () =>
  client.get<JoinRequestRead[]>('/join-requests').then((r) => r.data)

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
export const getSubmission = (teamId: string) =>
  client.get<SubmissionRead>(`/teams/${teamId}/submission`).then((r) => r.data)

export const createSubmission = (
  teamId: string,
  body: { github_url?: string | null; gdrive_url?: string | null },
) => client.post<SubmissionRead>(`/teams/${teamId}/submission`, body).then((r) => r.data)

export const updateSubmission = (
  teamId: string,
  body: { github_url?: string | null; gdrive_url?: string | null },
) => client.patch<SubmissionRead>(`/teams/${teamId}/submission`, body).then((r) => r.data)

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

export const adminPostAnnouncement = (title: string, body: string, image_url?: string | null) =>
  client
    .post<AnnouncementRead>('/admin/announcements', { title, body, image_url })
    .then((r) => r.data)

export const adminUpdateAnnouncement = (
  announcementId: string,
  body: { title?: string; body?: string; image_url?: string | null },
) =>
  client
    .patch<AnnouncementRead>(`/admin/announcements/${announcementId}`, body)
    .then((r) => r.data)

export const adminDeleteAnnouncement = (announcementId: string) =>
  client.delete(`/admin/announcements/${announcementId}`).then((r) => r.data)

// ---------- Admin — Submissions ----------
export const adminGetSubmissions = () =>
  client.get<AdminSubmissionRow[]>('/admin/submissions').then((r) => r.data)

export const adminSubmissionsCsv = () =>
  client
    .get<Blob>('/admin/submissions', { params: { format: 'csv' }, responseType: 'blob' })
    .then((r) => r.data)

export const adminSetDeadline = (submission_deadline_at: string) =>
  client
    .patch<EventSettingsRead>('/admin/submissions/deadline', { submission_deadline_at })
    .then((r) => r.data)
