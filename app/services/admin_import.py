import io

from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.security import hash_password_async
from app.db.models import Profile
from app.schemas.admin import (
    ImportConfirmRowIn,
    ImportConfirmResponse,
    ImportPreviewResponse,
    ImportRow,
)

REQUIRED_COLUMNS = ("name", "email", "student_staff_id")


def _parse_workbook(content: bytes) -> list[dict]:
    """Read the first sheet; header row must contain name, email, student_staff_id."""
    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception:
        raise ApiError(400, "File could not be parsed as an Excel (.xlsx) workbook")
    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)
    try:
        header = next(rows)
    except StopIteration:
        raise ApiError(400, "The uploaded sheet is empty")
    columns = {
        str(cell).strip().lower(): idx
        for idx, cell in enumerate(header)
        if cell is not None
    }
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise ApiError(
            400,
            f"Missing required column(s) in header row: {', '.join(missing)}. "
            f"Expected columns: {', '.join(REQUIRED_COLUMNS)}",
        )

    def cell(row: tuple, key: str) -> str | None:
        idx = columns[key]
        value = row[idx] if idx < len(row) else None
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    parsed = []
    for row_number, row in enumerate(rows, start=2):
        if all(v is None for v in row):
            continue  # skip fully blank rows
        parsed.append(
            {
                "row_number": row_number,
                "name": cell(row, "name"),
                "email": cell(row, "email"),
                "student_staff_id": cell(row, "student_staff_id"),
            }
        )
    if not parsed:
        raise ApiError(400, "The uploaded sheet has no data rows")
    return parsed


async def _existing_sets(db: AsyncSession) -> tuple[set[str], set[str]]:
    emails = {e.lower() for e in (await db.scalars(select(Profile.email))).all()}
    ids = {s.lower() for s in (await db.scalars(select(Profile.student_staff_id))).all()}
    return emails, ids


def _validate_rows(
    rows: list[dict], db_emails: set[str], db_ids: set[str]
) -> list[ImportRow]:
    """Flag each row individually — a bad row never rejects the whole file."""
    seen_emails: set[str] = set()
    seen_ids: set[str] = set()
    validated: list[ImportRow] = []
    for row in rows:
        issues: list[str] = []
        for field in REQUIRED_COLUMNS:
            if not row[field]:
                issues.append(f"missing {field}")
        email = (row["email"] or "").lower()
        sid = (row["student_staff_id"] or "").lower()
        if email:
            if email in db_emails:
                issues.append("email already registered")
            if email in seen_emails:
                issues.append("duplicate email within file")
            seen_emails.add(email)
        if sid:
            if sid in db_ids:
                issues.append("student_staff_id already registered")
            if sid in seen_ids:
                issues.append("duplicate student_staff_id within file")
            seen_ids.add(sid)
        validated.append(
            ImportRow(
                row_number=row["row_number"],
                name=row["name"],
                email=row["email"],
                student_staff_id=row["student_staff_id"],
                status="flagged" if issues else "ok",
                issues=issues,
            )
        )
    return validated


async def preview(db: AsyncSession, content: bytes) -> ImportPreviewResponse:
    """Step 1: parse and validate WITHOUT writing anything."""
    rows = _parse_workbook(content)
    db_emails, db_ids = await _existing_sets(db)
    validated = _validate_rows(rows, db_emails, db_ids)
    ok = sum(1 for r in validated if r.status == "ok")
    return ImportPreviewResponse(
        rows=validated, ok_count=ok, flagged_count=len(validated) - ok
    )


async def confirm(
    db: AsyncSession, rows: list[ImportConfirmRowIn]
) -> ImportConfirmResponse:
    """Step 2: re-validate and bulk-create accounts + profiles for clean rows.

    Initial password is the participant's student_staff_id; first_login forces
    an immediate change.
    """
    if not rows:
        raise ApiError(400, "No rows provided to import")
    raw = [
        {
            "row_number": i,
            "name": r.name.strip() or None,
            "email": r.email.strip() or None,
            "student_staff_id": r.student_staff_id.strip() or None,
        }
        for i, r in enumerate(rows, start=1)
    ]
    db_emails, db_ids = await _existing_sets(db)
    validated = _validate_rows(raw, db_emails, db_ids)

    created = 0
    skipped_rows: list[ImportRow] = []
    for row in validated:
        if row.status != "ok":
            skipped_rows.append(row)
            continue
        db.add(
            Profile(
                name=row.name,
                email=row.email,
                student_staff_id=row.student_staff_id,
                role="participant",
                first_login=True,
                hashed_password=await hash_password_async(row.student_staff_id),
            )
        )
        created += 1
    await db.commit()
    return ImportConfirmResponse(
        created=created, skipped=len(skipped_rows), skipped_rows=skipped_rows
    )
