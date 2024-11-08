import pytest
from httpx import AsyncClient
from fastapi import status


async def create_post(body: str, asyn_client: AsyncClient, logged_in_token: str) -> dict:
    response = await asyn_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_comment(body: str, post_id: int, asyn_client: AsyncClient,
                         logged_in_token: str) -> dict:
    response = await asyn_client.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def like_post(post_id: int, asyn_client: AsyncClient,
                    logged_in_token: str) -> dict:
    response = await asyn_client.post(
        "/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str) -> dict:
    return await create_post("The Post", async_client, logged_in_token)


@pytest.fixture()
async def created_comment(async_client: AsyncClient, created_post: dict, logged_in_token: str):
    return await create_comment("The Comment", created_post["id"], async_client, logged_in_token)


@pytest.fixture()
async def liked_post(async_client: AsyncClient, created_post: dict, logged_in_token: str):
    return await like_post(created_post["id"], async_client, logged_in_token)


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient, registered_user: dict, logged_in_token: str):
    body = "The Post"
    response = await async_client.post(
        "/post",
        json={"body": body, "user_id": registered_user["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )

    assert response.status_code == 201
    assert {"id": 1, "body": "The Post", "user_id": registered_user["id"]}.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_no_body(async_client: AsyncClient, registered_user: dict, logged_in_token: str):
    res = await async_client.post("/post", json={}, headers={"Authorization": f"Bearer {logged_in_token}"})

    assert res.status_code == 422


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    res = await async_client.get("/post")

    assert res.status_code == 200
    assert res.json() == [{**created_post, "likes": 0}]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting,order",
    [
        ("new", [2, 1]),
        ("old", [1, 2]),
        ("most_likes", [1, 2]),
    ]
)
async def test_get_all_posts_sorted(async_client: AsyncClient, logged_in_token: str, sorting: str, order: list[int]):
    await create_post("Demo 1", async_client, logged_in_token)
    await create_post("Demo 2", async_client, logged_in_token)
    if sorting == "most_likes":
        await like_post(1, async_client, logged_in_token)
    res = await async_client.get("/post", params={"sorting": sorting})

    assert res.status_code == 200
    posts = res.json()
    post_ids = [p["id"] for p in posts]
    assert post_ids == order


@pytest.mark.anyio
async def test_get_all_posts_wrong_sort(async_client: AsyncClient):
    res = await async_client.get("/post", params={"sorting": "wrong"})
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_get_all_posts_empty(async_client: AsyncClient):
    res = await async_client.get("/post")

    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict, registered_user: dict,
                              logged_in_token: str):
    body = "The Comment"
    post_id = created_post["id"]
    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": post_id, "user_id": registered_user["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )

    assert response.status_code == 201
    assert {
               "id": 1,
               "body": body,
               "post_id": post_id,
               "user_id": registered_user["id"]
           }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_all_post_comments(
        async_client: AsyncClient, created_post: dict, created_comment: dict
):
    res = await async_client.get(f"/post/{created_post['id']}/comment")

    assert res.status_code == 200
    assert res.json() == [created_comment]


@pytest.mark.anyio
async def test_get_post_comments(
        async_client: AsyncClient, created_post: dict, created_comment: dict
):
    res = await async_client.get(f"/post/{created_post['id']}")

    assert res.status_code == 200
    assert res.json() == {
        "post": {**created_post, "likes": 0},
        "comments": [created_comment],
    }


@pytest.mark.anyio
async def test_get_all_post_comments_no_post(
        async_client: AsyncClient, created_post: dict, created_comment: dict
):
    res = await async_client.get("/post/-1/comment")

    assert res.status_code == 404


@pytest.mark.anyio
async def test_like_post(async_client: AsyncClient, created_post: dict, registered_user: dict,
                         logged_in_token: str):
    post_id = created_post["id"]
    response = await async_client.post(
        "/like",
        json={"post_id": post_id, "user_id": registered_user["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )

    assert response.status_code == 201
    assert {
               "id": 1,
               "post_id": post_id,
               "user_id": registered_user["id"]
           }.items() <= response.json().items()
