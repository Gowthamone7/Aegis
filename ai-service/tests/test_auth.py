"""
Unit tests for EKA Authentication & Authorization
"""
import pytest
from eka.auth import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
    DEVELOPER,
    MANAGER,
    VIEWER,
    ADMIN,
)


def test_password_hashing():
    pw = "demo123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrongpw", hashed) is False


def test_jwt_create_and_decode():
    token = create_token("dev@acme", "acme", DEVELOPER)
    assert token is not None
    payload = decode_token(token)
    assert payload["sub"] == "dev@acme"
    assert payload["tenant"] == "acme"
    assert payload["role"] == DEVELOPER


def test_jwt_invalid_token():
    with pytest.raises(Exception):
        decode_token("invalid.token.signature")

