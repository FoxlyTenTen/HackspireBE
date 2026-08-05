 HACKSPIRE: LUMINA — Backend API Server (FastAPI + Swagger)

 Context

 Greenfield build of the complete backend for the HACKSPIRE: LUMINA hackathon platform, per the detailed spec provided. Backend only — no frontend. The functional target is a running FastAPI app whose /docs (Swagger UI) fully documents ~30 endpoints across 11 tag groups, backed by real service-layer logic: teams with leader/capacity/lock rules, join requests, submissions with deadline enforcement, Excel-based participant import, and polling notifications.

 Current repo state: essentially empty — one prior commit, a venv/ with all required packages already installed (fastapi 0.141, SQLAlchemy 2.0.51 async, asyncpg, aiosqlite, python-jose, bcrypt 5.0, openpyxl, pydantic-settings, python-multipart, uvicorn), Python 3.13, and a .env containing DATABASE_URL (Supabase Postgres). app/test_db_connection.py exists and stays untouched.

 Decisions (resolved with user)

 - Passwords: add hashed_password column to profiles (stand-in for Supabase auth.users). Seed an admin on startup from env (ADMIN_EMAIL/ADMIN_PASSWORD, dev defaults admin@hackspire.dev / admin123) if no admin exists.
 - Excel import initial password = the participant's student_staff_id; first_login=true forces change.
 - Event info (sponsors, prize pool, contact): static constants in config; countdown + timeline from DB.
 - Hashing: use bcrypt package directly — installed passlib 1.7.4 is incompatible with bcrypt 5.0 (reads removed __about__). Do NOT import passlib.
 - JWT: python-jose, HS256, sub=profile id, role claim, exp from settings (default 24h).
 - Login username matches either email or student_staff_id.
 - Tables: Base.metadata.create_all on startup (async lifespan). No Alembic this pass.
 - Race guard: SELECT ... FOR UPDATE (with_for_update()) on the team row in join/add-member/approve paths. On SQLite it's a no-op but writes are serialized anyway — acceptable.
 - UUIDs: SQLAlchemy Uuid type + uuid4 defaults (portable across PG/SQLite). Timestamps DateTime(timezone=True), always UTC.
 - DB URL: from DATABASE_URL env; if unset → sqlite+aiosqlite:///./hackspire.db. Normalize postgresql:// → postgresql+asyncpg://.
 - File storage: StorageBackend interface with LocalDiskStorage writing to ./uploads/ (swappable for Supabase Storage later).

 Project structure (all new files)

 app/
   main.py                    # FastAPI app, title="HACKSPIRE: LUMINA API", version 0.1.0, lifespan (create_all + seed admin), routers mounted at /api/v1
   dependencies.py            # get_db, get_current_user, require_admin, require_team_leader(team_id), require_team_member(team_id)
   core/
     config.py                # pydantic-settings: DATABASE_URL, JWT_SECRET, JWT_EXPIRES_MIN, ADMIN_EMAIL/PASSWORD, UPLOAD_DIR, static EVENT_INFO constants
     security.py              # bcrypt hash/verify, JWT create/decode
   db/
     base.py                  # DeclarativeBase
     session.py               # async engine + sessionmaker + get_db
     models.py                # all 12 tables per spec (+ hashed_password on profiles)
   schemas/
     common.py                # ErrorResponse {"error": str} — referenced on every 4xx/409 via a shared `responses={...}` helper dict
     auth.py, profile.py, team.py, join_request.py, submission.py,
     event.py, notification.py, admin.py   # Read/Create/Update variants per table, with Field(examples=...) on login, team create, submission, import preview, approve/reject
   routers/
     auth.py                  # tag "Auth"
     content.py               # tag "Home / Content" — /event/info, /materials, /finalists, /winners
     participants.py          # tag "Participants"
     teams.py                 # tag "Teams"
     join_requests.py         # tag "Join Requests"
     notifications.py         # tag "Notifications"
     submissions.py           # tag "Submission" — /teams/{id}/submission
     admin_participants.py    # tag "Admin — Participants"
     admin_teams.py           # tag "Admin — Teams"
     admin_content.py         # tag "Admin — Event Content"
     admin_submissions.py     # tag "Admin — Submissions"
   services/
     auth.py, teams.py, join_requests.py, submissions.py,
     notifications.py, admin_import.py, content.py
     storage.py               # StorageBackend ABC + LocalDiskStorage
 .env.example
 requirements.txt             # pinned to versions already in venv
 README.md                    # run instructions, seeded admin creds, Swagger at /docs

 Models (db/models.py) — per spec, notes only where non-obvious

 - profiles: + hashed_password (nullable text). role in (participant|admin) via CHECK or app-level validation.
 - teams.capacity default 5; enforce max 5 and >= member count in service layer.
 - team_members.participant_id UNIQUE (one team at a time).
 - join_requests: partial-unique "one pending per participant" — enforce in service layer inside the locked transaction (portable across SQLite/PG; a PG partial index can come later).
 - submissions.team_id UNIQUE; event_settings single row id=1; rest exactly as spec'd.

 Business rules — where each lives (services layer)

 - teams service: create (creator must be team-less → becomes leader), edit (capacity ≤5 and ≥ member count; auto-flip status to full when count==capacity, and un-full when a slot opens), delete (leader-only, = leader leaving), add member (leader, target must be unassigned, capacity check under row lock, team_update notification to existing members), remove member, leave (non-leader only; leader gets 400 pointing to delete), all writes blocked when locked=true → 409.
 - join_requests service: create (requester team-less, no other pending request, team not locked/full), leader respond approve/reject under team row lock (approve re-checks capacity → 409 if full raced), sets responded_at, notifies requester (join_response) and members (team_update on approve). Auto-reject other pending requests of that participant on approve.
 - submissions service: URL regex for github.com/... or Google Drive (drive.google.com / docs.google.com); reject writes when now > submission_deadline_at → 409/400 per spec.
 - admin_import service: parse xlsx (openpyxl) expecting columns name, email, student_staff_id → preview rows each flagged ok | duplicate_email | missing_field (checked against file AND DB); confirm re-validates and bulk-creates profiles (password = student_staff_id, first_login=true), skipping flagged rows, returns created/skipped counts.
 - admin teams: approve → approval_status=approved, locked=true, status=closed; reject → approval_status=rejected, optional admin_note, stays editable; PATCH can reassign leader_id (new leader must be a member) and unlock; force-delete cascades.
 - announcements: create + fan-out announcement notifications to all participants.
 - auth service: login (username=email or student_staff_id) → {jwt, first_login}; change-password (bcrypt, clears first_login). Non-admin users with first_login=true are blocked by get_current_user from everything except change-password → 403.

 Swagger requirements

 - Every route: summary, description, response_model, explicit status_code (201 create, 204 delete), and responses={401: {...}, 403: {...}, ...} referencing ErrorResponse — build one error_responses(*codes) helper in schemas/common.py so it's uniform.
 - Custom exception type (ApiError(status, message)) + handler producing {"error": msg}; also override the default HTTPException handler so all errors match the shape.
 - Field(examples=[...]) / json_schema_extra on the five spec'd example payloads.
 - HTTPBearer security scheme so Swagger shows the Authorize button.

 Implementation order

 1. core/config.py, db/base.py, db/session.py, db/models.py
 2. core/security.py, schemas/common.py + all schemas
 3. dependencies.py (guards), main.py skeleton (lifespan: create_all + seed admin)
 4. Services + routers, group by group (auth → teams/join-requests → content/notifications → submissions → admin)
 5. .env.example, requirements.txt (pin installed versions), README.md
 6. Verification pass

 Verification

 1. venv\Scripts\uvicorn app.main:app --reload starts clean (run once with DATABASE_URL unset → SQLite fallback; keep real .env untouched for their Supabase runs).
 2. Fetch /openapi.json; assert all ~30 paths present, grouped under the 11 exact tags, no generic dict request bodies.
 3. Smoke script (scratchpad, httpx against the live server): login as seeded admin → import-preview a generated xlsx → confirm → login as participant (forced change-password flow) → create team → second participant join-request → leader approve → admin approve (verify lock blocks subsequent PATCH with 409) → submission URL validation (bad URL 400, GitHub URL ok) → deadline set in past blocks PATCH → notifications poll shows join_response/team_update/announcement.
 4. /docs loads and renders example payloads.