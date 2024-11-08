import datetime
import logging
from typing import Annotated, Literal

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, ExpiredSignatureError, JWTError

from passlib.context import CryptContext

from storeapi.database import user_table, database

logger = logging.getLogger(__name__)

SECRET_KEY = "9b73f2a1bdd7ae163444473d29a6885ffa22ab26117068f72a5a56a74d12d1fc"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"])

def create_unauthorized_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def access_token_expire_minutes() -> int:
    return 30


def confirm_token_expire_minutes() -> int:
    return 1440


def create_access_token(email: str):
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_confirmation_token(email: str):
    logger.debug("Creating confirmation token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "confirmation"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password_hash(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


async def authenticate_user(email: str, password: str):
    logger.debug("Authenticating user", extra={"email": email})
    user = await get_user(email)
    if not user:
        raise create_unauthorized_exception("Could not validate credentials")
    if not verify_password_hash(password, user.password):
        raise create_unauthorized_exception("Could not validate credentials")
    if not user.confirmed:
        raise create_unauthorized_exception("User has not confirmed email")
    return user


async def get_user(email: str):
    query = user_table.select().where(user_table.c.email == email)
    logger.debug(query)
    result = await database.fetch_one(query)
    if result:
        return result


def get_subject_for_token_type(
        token: str, type: Literal["access", "confirmation"]
) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as e:
        raise create_unauthorized_exception("Token has expired") from e
    except JWTError as e:
        raise create_unauthorized_exception("Invalid token") from e

    email = payload.get("sub")
    if email is None:
        raise create_unauthorized_exception("Token is missing 'sub' field")

    token_type = payload.get("type")
    if token_type is None or token_type != type:
        raise create_unauthorized_exception(
            f"Token has incorrect type, expected '{type}'"
        )

    return email


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    email = get_subject_for_token_type(token, "access")
    user = await get_user(email=email)
    if user is None:
        raise create_unauthorized_exception("Could not validate credentials")
    return user
