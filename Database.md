# HACKSPIRE: LUMINA — Database Schema

## profiles
Extends Supabase's built-in `auth.users` — one row per login account, participant or admin.

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK, matches `auth.users.id` |
| name | text | |
| email | text | unique |
| student_staff_id | text | unique — used for dedup on Excel import |
| role | text | `participant` \| `admin` |
| first_login | boolean | default true, forces password change |
| hashed_password | | |
| created_at | timestamptz | |

## teams

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| name | text | unique |
| leader_id | uuid | FK → profiles.id |
| capacity | int | default 5, max 5, ≥ current member count |
| status | text | `open` \| `looking_for_teammates` \| `closed` \| `full` |
| approval_status | text | `pending` \| `approved` \| `rejected` |
| admin_note | text | nullable — set on rejection |
| locked | boolean | default false — true on admin approval, blocks writes |
| created_at | timestamptz | |

## team_members

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| team_id | uuid | FK → teams.id, ON DELETE CASCADE |
| participant_id | uuid | FK → profiles.id, unique — one team at a time |
| joined_at | timestamptz | |

## join_requests
Unique constraint: one pending request per participant_id at a time.

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| team_id | uuid | FK → teams.id, ON DELETE CASCADE |
| participant_id | uuid | FK → profiles.id |
| status | text | `pending` \| `approved` \| `rejected` |
| created_at | timestamptz | |
| responded_at | timestamptz | nullable |

## submissions

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| team_id | uuid | FK → teams.id, unique, ON DELETE CASCADE |
| url | text | validated as GitHub or Google Drive link |
| submitted_at | timestamptz | |
| updated_at | timestamptz | |

## event_settings
Single-row config table.

| Column | Type | Notes |
|---|---|---|
| id | int | PK, always 1 |
| countdown_at | timestamptz | event start |
| submission_deadline_at | timestamptz | |
| updated_at | timestamptz | |

## timeline_items

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| time_label | text | e.g. "10:00 AM" |
| title | text | |
| description | text | nullable |
| order_index | int | for manual ordering |

## finalists

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| team_id | uuid | FK → teams.id |
| published | boolean | default false |
| published_at | timestamptz | nullable |

## winners

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| team_id | uuid | FK → teams.id |
| placement | text | e.g. 1st, 2nd, 3rd |
| published | boolean | default false |
| published_at | timestamptz | nullable |

## materials

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| file_name | text | |
| file_url | text | public bucket URL |
| uploaded_by | uuid | FK → profiles.id (admin) |
| uploaded_at | timestamptz | |

## announcements

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| title | text | |
| body | text | |
| posted_by | uuid | FK → profiles.id (admin) |
| posted_at | timestamptz | |

## notifications
team_update fires for every existing team member (not the new joiner) whenever someone joins the team.

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| participant_id | uuid | FK → profiles.id — recipient |
| type | text | `join_request` \| `join_response` \| `announcement` \| `team_update` |
| reference_id | uuid | nullable — points to join_requests.id, announcements.id, or teams.id |
| message | text | |
| read | boolean | default false |
| created_at | timestamptz | |

## Relationships Summary
- profiles 1—N teams (as leader)
- teams 1—N team_members N—1 profiles — cascades on team delete
- teams 1—N join_requests N—1 profiles — cascades on team delete
- teams 1—1 submissions — cascades on team delete
- teams 1—1 finalists (optional)
- teams 1—1 winners (optional)
- profiles 1—N materials (as uploader)
- profiles 1—N announcements (as poster)
- profiles 1—N notifications (as recipient)