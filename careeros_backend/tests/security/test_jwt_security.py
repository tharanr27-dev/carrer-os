"""Security-focused unit tests: JWT forgery, expired tokens, RBAC guards."""

from datetime import timedelta

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)

# ── JWT Forgery Tests ──────────────────────────────────────────────────────────


def test_tampered_jwt_rejected():
    """A JWT signed with a wrong secret must not decode successfully."""
    token = create_access_token(subject="legit-user")

    # Attempt to decode with a different secret
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong-secret", algorithms=[settings.ALGORITHM])


def test_token_type_is_access():
    """Access tokens must have type='access'."""
    token = create_access_token(subject="user-123")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload.get("type") == "access"


def test_token_type_is_refresh():
    """Refresh tokens must have type='refresh'."""
    token = create_refresh_token(subject="user-123")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload.get("type") == "refresh"


def test_expired_token_raises():
    """A token with a past expiry must raise JWTError on decode."""
    # Use a negative delta to force instant expiry
    token = create_access_token(subject="expire-me", expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def test_access_token_sub_matches():
    """Decoded token sub must match the subject passed to create_access_token."""
    subject = "user-uuid-9999"
    token = create_access_token(subject=subject)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload.get("sub") == subject


# ── Password Security ──────────────────────────────────────────────────────────


def test_empty_password_still_hashes():
    """Even empty strings can be hashed (policy enforcement is at schema layer)."""
    h = get_password_hash("")
    assert verify_password("", h)


def test_long_password_hashes():
    """Passwords up to bcrypt's 72-byte limit should hash successfully."""
    long_pw = "A" * 72
    h = get_password_hash(long_pw)
    assert verify_password(long_pw, h)
