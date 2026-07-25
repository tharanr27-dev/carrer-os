"""Unit tests for auth schemas validation."""

import pytest
from pydantic import ValidationError

from app.modules.auth.schemas import UserCreate, UserLogin


def test_user_create_valid():
    user = UserCreate(
        email="test@example.com",
        password="SecurePass123!",
    )
    assert user.email == "test@example.com"


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            password="SecurePass123!",
        )


def test_user_create_missing_password():
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com")


def test_user_login_valid():
    login = UserLogin(email="test@example.com", password="pass123")
    assert login.email == "test@example.com"


def test_user_login_missing_fields():
    with pytest.raises(ValidationError):
        UserLogin(email="missing@example.com")
