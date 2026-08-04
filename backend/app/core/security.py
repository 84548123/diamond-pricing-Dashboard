"""Small dependency-based protection for shared dashboard write operations."""

import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def require_admin_key(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> None:
    """Require the deployment's admin secret before shared data can be changed."""
    expected_key = settings.ADMIN_API_KEY.strip()
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Uploads are disabled until ADMIN_API_KEY is configured by an administrator.",
        )
    if not x_admin_key or not hmac.compare_digest(x_admin_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid administrator key is required to change shared dashboard data.",
        )
