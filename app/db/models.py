import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Profile(Base):
    """Extends auth.users in Supabase — id matches auth.users.id for accounts
    created through the invite flow; auth itself is handled by Supabase Auth."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True)
    student_staff_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    role: Mapped[str] = mapped_column(Text, default="participant")  # participant | admin
    # first_login: only set by admin password resets now (forces a change on
    # next login); obsolete for invited accounts.
    first_login: Mapped[bool] = mapped_column(Boolean, default=True)
    # invited (email sent, not yet accepted) | active (password set / logged in)
    # | failed (reserved for SMTP bounce webhooks — never set by the app yet)
    invite_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    username: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    reference_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    university_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_role: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    membership: Mapped["TeamMember | None"] = relationship(
        back_populates="participant", uselist=False
    )


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, unique=True)
    # DB-generated on INSERT via a Postgres sequence + trigger, format GR_01, GR_02...
    # Never set this from app code — call db.refresh(team) after insert to load it.
    reference_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    leader_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profiles.id"))
    capacity: Mapped[int] = mapped_column(Integer, default=5)
    # open | looking_for_teammates | closed | full
    status: Mapped[str] = mapped_column(Text, default="open")
    # pending | approved | rejected
    approval_status: Mapped[str] = mapped_column(Text, default="pending")
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    leader: Mapped[Profile] = relationship(foreign_keys=[leader_id])
    members: Mapped[list["TeamMember"]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )
    join_requests: Mapped[list["JoinRequest"]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )
    submission: Mapped["Submission | None"] = relationship(
        back_populates="team", uselist=False, cascade="all, delete-orphan"
    )


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("teams.id", ondelete="CASCADE"), index=True
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id"), unique=True  # one team at a time
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    team: Mapped[Team] = relationship(back_populates="members")
    participant: Mapped[Profile] = relationship(back_populates="membership")


class JoinRequest(Base):
    __tablename__ = "join_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("teams.id", ondelete="CASCADE"), index=True
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id"), index=True
    )
    # pending | approved | rejected — "one pending per participant" enforced in the
    # service layer inside the locked transaction (portable across SQLite/Postgres)
    status: Mapped[str] = mapped_column(Text, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    team: Mapped[Team] = relationship(back_populates="join_requests")
    participant: Mapped[Profile] = relationship()


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("teams.id", ondelete="CASCADE"), unique=True
    )
    github_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    gdrive_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("profiles.id"), nullable=True
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    team: Mapped[Team] = relationship(back_populates="submission")


class EventSettings(Base):
    """Single-row config table: id is always 1."""

    __tablename__ = "event_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    countdown_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submission_deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class TimelineItem(Base):
    __tablename__ = "timeline_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    bootcamp_name: Mapped[str] = mapped_column(Text)
    date_label: Mapped[str] = mapped_column(Text)
    time_session: Mapped[str] = mapped_column(Text)
    session_type: Mapped[str] = mapped_column(Text)
    speaker_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    speaker_bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    speaker_photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # TBD | Proposed | Confirmed | Declined — admin-facing
    status: Mapped[str] = mapped_column(Text, default="TBD")
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)


class Finalist(Base):
    __tablename__ = "finalists"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("teams.id"))
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    team: Mapped[Team] = relationship()


class Winner(Base):
    __tablename__ = "winners"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("teams.id"))
    placement: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    team: Mapped[Team] = relationship()


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    file_name: Mapped[str] = mapped_column(Text)
    file_url: Mapped[str] = mapped_column(Text)
    # general | submission_template
    category: Mapped[str] = mapped_column(Text, default="general")
    uploaded_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profiles.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profiles.id"))
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profiles.id"))
    action: Mapped[str] = mapped_column(Text)
    target_table: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    admin: Mapped[Profile] = relationship()


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    participant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id"), index=True
    )
    # join_request | join_response | announcement | team_update
    type: Mapped[str] = mapped_column(Text)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
