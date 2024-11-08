import pytest
from fastapi import status, Request
from httpx import AsyncClient


async def register_user(async_client: AsyncClient, email: str, password: str):
    return await async_client.post(
        "/register",
        json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_register(async_client: AsyncClient):
    newuser = {"email": "maun@test.com", "password": "12345"}
    response = await register_user(async_client, newuser["email"], newuser["password"])

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.anyio
async def test_register_exits(async_client: AsyncClient, registered_user: dict):
    response = await register_user(async_client, registered_user["email"], registered_user["password"])

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.anyio
async def test_confirm_user(async_client: AsyncClient, mocker):
    spy = mocker.spy(Request, "url_for")
    await register_user(async_client, "maun@test.com", "12345")

    # We only call Request.url_for once, so this is OK.
    # This is not a scalable solution.
    # A better solution will be discussed in the next couple lectures.
    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)

    assert response.status_code == 200
    assert "User confirmed" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user_invalid_token(async_client: AsyncClient):
    response = await async_client.get("/confirm/invalid_token")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_confirm_user_expired_token(async_client: AsyncClient, mocker):
    mocker.patch("storeapi.security.confirm_token_expire_minutes", return_value=-1)
    spy = mocker.spy(Request, "url_for")
    await register_user(async_client, "maun@test.com", "12345")

    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)

    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    response = await async_client.post(
        "/token", data={"username": "maun@test.com", "password": "12345"}
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post(
        "/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
