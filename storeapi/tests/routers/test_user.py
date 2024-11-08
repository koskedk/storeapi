import pytest
from fastapi import status
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
