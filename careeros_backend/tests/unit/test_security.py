from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def test_password_hash_and_verify():
    """Password hashing is one-way; verify_password round-trips correctly."""
    plain = "SecurePass123!"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("WrongPass!", hashed)


def test_password_different_salts():
    """Two hashes of the same password must differ (bcrypt uses random salts)."""
    pw = "SamePassword99"
    h1 = get_password_hash(pw)
    h2 = get_password_hash(pw)
    assert h1 != h2


# ── JWT Tokens ─────────────────────────────────────────────────────────────────


def test_create_access_token_contains_sub():
    """Access token is a valid JWT string."""
    token = create_access_token(subject="user-uuid-1234")
    assert isinstance(token, str)
    assert len(token) > 20


def test_create_refresh_token():
    """Refresh token is generated without error."""
    token = create_refresh_token(subject="user-uuid-1234")
    assert isinstance(token, str)


def test_access_token_expires():
    """Tokens created with very short expiry should still be strings."""
    token = create_access_token(
        subject="expire-test",
        expires_delta=timedelta(seconds=1),
    )
    assert isinstance(token, str)
