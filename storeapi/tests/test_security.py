import pytest
import logging

from jose import jwt

from storeapi import security

logger = logging.getLogger(__name__)


def test_get_password_hash():
    password = "abcd!"
    hashed = security.get_password_hash(password)
    assert hashed != password


def test_get_password_hash_is_unique():
    password = "abcd!"
    hashed01 = security.get_password_hash(password)
    hashed02 = security.get_password_hash(password)
    assert hashed01 != hashed02
    print("\n")
    print(f"{hashed01} != {hashed02}")


def test_verif_password_hash():
    password = "abcd!"
    assert security.verify_password_hash(
        password,
        security.get_password_hash(password)
    )


def test_access_token_expire_minutes():
    assert security.access_token_expire_minutes() == 30


def test_create_access_token():
    token = security.create_access_token("123")
    assert {"sub": "123"}.items() <= jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])

    assert user.email == registered_user["email"]

@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example.com")
    assert user is None

@pytest.mark.anyio
async def test_authenticate_user(registered_user: dict):
    user = await security.authenticate_user(
        registered_user["email"], registered_user["password"]
    )
    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(registered_user["email"], "wrong password")


@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)
    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid token")
