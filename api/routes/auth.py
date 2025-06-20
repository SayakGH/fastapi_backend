# api/routes/auth.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ..schemas import db
import api.utils as utils
from ..Oauth2 import create_access_token

router = APIRouter(
    prefix="/login",
    tags=["Authentication"]
)

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("", status_code=status.HTTP_200_OK)
async def login(credentials: LoginRequest):
    # pick your users collection
    users_col = db["users"]                 # <— here

    # now call .find_one on the collection
    user = await db["users"].find_one({"name": credentials.username})

    if not user or not utils.verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid username or password"
        )

    access_token = create_access_token({"id": str(user["_id"])})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
