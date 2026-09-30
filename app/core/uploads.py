"""Shared upload size limits.

Admin-only surface (every upload route is behind require_admin), so the
blast radius of a huge/malicious file is a trusted admin account, not an
anonymous DoS vector — but nothing anywhere previously capped upload size at
all, so a single oversized file (accidental or otherwise) could exhaust
worker memory. These caps are generous for real usage, not a tight quota.
"""

from app.core.errors import ApiError

MAX_EXCEL_BYTES = 10 * 1024 * 1024  # 10 MB — participant/timeline roster imports
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB — announcement images, material files


def check_upload_size(content: bytes, max_bytes: int, label: str) -> None:
    if len(content) > max_bytes:
        raise ApiError(413, f"{label} is too large (max {max_bytes // (1024 * 1024)}MB)")
