import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


def log_admin_action(
    db: AsyncSession,
    admin_id: uuid.UUID,
    action: str,
    *,
    target_table: str | None = None,
    target_id: uuid.UUID | None = None,
    details: str | None = None,
) -> AuditLog:
    """Stage an audit_log row; call before the caller's own db.commit()."""
    entry = AuditLog(
        admin_id=admin_id,
        action=action,
        target_table=target_table,
        target_id=target_id,
        details=details,
    )
    db.add(entry)
    return entry
