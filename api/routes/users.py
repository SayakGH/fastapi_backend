from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas import User,db, UserResponse,TokenData
from fastapi.encoders import jsonable_encoder
from ..utils import get_password_hash
import secrets
from ..send_mail import send_registration_mail
from ..Oauth2 import get_current_user
from bson import ObjectId

router = APIRouter(
    tags=["User Routes"],
)

@router.post("/registration", response_description="User registration", response_model=UserResponse)
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

    #send mail
    await send_registration_mail("Regisreation Successful", user["email"],{
        "title":"Registration Successful",
        "name": user["name"],
    })


    return created_user

@router.get("/details", response_model=UserResponse)
async def details(current_user: TokenData = Depends(get_current_user)):
    # current_user.id is a string; convert if your DB uses ObjectId
    user = await db["users"].find_one({"_id": current_user.id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user = jsonable_encoder(user)
    return user