import logging
from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from storeapi.database import user_table, database
from storeapi.models.user import UserIn
from storeapi.security import get_user, get_password_hash, authenticate_user, create_access_token, \
    get_subject_for_token_type, create_confirmation_token

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserIn, request: Request):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists"
        )
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(
        email=user.email,
        password=hashed_password
    )
    logger.debug(query)
    await database.execute(query)
    return {
        "detail": "User created. Please confirm your email.",
        "confirmation_url": request.url_for(
            "confirm_email", token=create_confirmation_token(user.email)
        ),
    }


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirm/{token}")
async def confirm_email(token: str):
    email = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )

    logger.debug(query)

    await database.execute(query)
    return {"detail": "User confirmed"}
