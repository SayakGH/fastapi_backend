# api/Oauth2.py

import os
from dotenv import load_dotenv
from fastapi import HTTPException, Header, status
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from .schemas import TokenData  # your Pydantic model

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


def create_access_token(data: dict) -> str:
    """
    Create a JWT with an expiry (in minutes).
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_access_token(token: str) -> TokenData:
    """
    Decode the JWT. Raise a 401 HTTPException on any failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
    except JWTError:
        raise credentials_exception

    # Try both "id" or "_id" if that's what you encoded
    user_id = payload.get("id") 
    if not user_id:
        raise credentials_exception
    return TokenData(id=str(user_id))


async def get_current_user(
    authorization: str = Header(..., alias="Authorization",
                              description="Bearer <token>")
) -> TokenData:
    """
    FastAPI dependency to:
    1. Read the Authorization header
    2. Split out the Bearer token
    3. Verify it and return TokenData
    """
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = parts[1]
    return verify_access_token(token)
