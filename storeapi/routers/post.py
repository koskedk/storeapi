import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, HTTPException, Depends
from storeapi.database import comment_table, post_table, like_table, database

from storeapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
    PostLike,
    PostLikeIn, UserPostWithLikes,
)
from storeapi.models.user import User
from storeapi.security import get_current_user

router = APIRouter()

logger = logging.getLogger(__name__)

select_post_likes_count_query = (
    sqlalchemy
    .select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


@router.get("/")
async def root():
    logger.info("Root GET called")
    info = {"status": "Store API running..."}
    logger.info("Done", extra={"email": "danmegga@gmail.com"})
    return info


async def find_post(post_id: int):
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(query)
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
        post: UserPostIn,
        current_user: Annotated[User, Depends(get_current_user)]
):
    data = {**post.model_dump(), "user_id": current_user.id}
    query = post_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)
    new_post = {**data, "id": last_record_id}
    return new_post


class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


@router.get("/post", response_model=list[UserPostWithLikes])
async def get_all_posts(sorting: PostSorting = PostSorting.new):
    query = select_post_likes_count_query

    if sorting == PostSorting.new:
        query = query.order_by(post_table.c.id.desc())
    if sorting == PostSorting.old:
        query = query.order_by(post_table.c.id.asc())
    if sorting == PostSorting.most_likes:
        query = query.order_by(sqlalchemy.desc("likes"))

    logger.debug(query)
    return await database.fetch_all(query)


# ---
@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(
        comment: CommentIn,
        current_user: Annotated[User, Depends(get_current_user)]
):
    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found!")
    data = {**comment.model_dump(), "user_id": current_user.id}
    query = comment_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)
    new_comment = {**data, "id": last_record_id}
    return new_comment


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_post_comments(post_id: int):
    post = await find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found!")

    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug(query)
    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    query = select_post_likes_count_query.where(post_table.c.id == post_id)
    logger.debug(query)
    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="post not found!")

    return {"post": post, "comments": await get_post_comments(post_id)}


@router.post("/like", response_model=PostLike, status_code=201)
async def like_post(
        like: PostLikeIn,
        current_user: Annotated[User, Depends(get_current_user)]
):
    post = await find_post(like.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found!")

    data = {**like.model_dump(), "user_id": current_user.id}
    query = like_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)
    new_like_post = {**data, "id": last_record_id}
    return new_like_post
