from fastapi import APIRouter, HTTPException, status
from ..schemas import User,db, UserResponse
from fastapi.encoders import jsonable_encoder
from ..utils import get_password_hash
import secrets

router = APIRouter(
    tags=["User Routes"],
)

@router.post("/registration", response_description="User registration")
async def registration(user: User):
    user = jsonable_encoder(user)
    

    username_found = await db["users"].find_one({"name": user["name"]})
    email_found = await db["users"].find_one({"email":user["email"]})

    if username_found:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Username already exists")
    
    if email_found:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already exists")
    
    user["password"] = get_password_hash(user["password"])
    user['apiKey'] = secrets.token_hex(30)

    new_user = await db['users'].insert_one(user)
    created_user = await db['users'].find_one({"_id": new_user.inserted_id})

    return created_user
