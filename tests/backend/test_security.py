from datetime import timedelta

import pytest

from backend.app.core.security import (
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_password_hash_is_not_plaintext():
    password = "SecurePassword123!"

    hashed_password = hash_password(password)

    assert hashed_password != password


def test_correct_password_is_verified():
    password = "SecurePassword123!"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True


def test_incorrect_password_is_rejected():
    hashed_password = hash_password("SecurePassword123!")

    assert (
        verify_password(
            "IncorrectPassword123!",
            hashed_password,
        )
        is False
    )


def test_access_token_can_be_created_and_decoded():
    token = create_access_token(
        subject="test-user",
        role="fraud_analyst",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "test-user"
    assert payload["role"] == "fraud_analyst"
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload


def test_invalid_access_token_is_rejected():
    with pytest.raises(TokenValidationError):
        decode_access_token("not-a-valid-token")


def test_expired_access_token_is_rejected():
    token = create_access_token(
        subject="expired-user",
        role="viewer",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(TokenValidationError):
        decode_access_token(token)


def test_refresh_token_is_random_and_hashable():
    first_token = create_refresh_token()
    second_token = create_refresh_token()

    assert first_token != second_token
    assert len(first_token) >= 32
    assert len(hash_refresh_token(first_token)) == 64
    assert hash_refresh_token(first_token) != first_token
