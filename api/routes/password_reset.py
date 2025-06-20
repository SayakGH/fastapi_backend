# library imports
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status

# module imports
from ..schemas import PasswordReset, PasswordResetRequest, db, TokenData
from ..send_mail import password_reset
from ..Oauth2 import create_access_token, get_current_user, verify_access_token
from ..utils import get_password_hash

router = APIRouter(
    prefix="/password",
    tags=["Password Reset"]
)


@router.post("/request/", response_description="Password reset request")
async def reset_request(user_email: PasswordResetRequest):
    user = await db["users"].find_one({"email": user_email.email})

    print(user)

    if user is not None:
        token = create_access_token({"id": user["_id"]})

        reset_link = f"http://localhost:8000/reset?token={token}"

        await password_reset("Password Reset", user["email"],
            {
                "title": "Password Reset",
                "name": user["name"],
                "reset_link": reset_link
            }
        )
        return {"msg": "Email has been sent with instructions to reset your password."}

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Your details not found, invalid email address"
        )


@router.put("/reset", response_description="Password reset")
async def reset(
    new_password: PasswordReset,
    token: str = Query(..., description="Your password-reset JWT")
):
    try:
        token_data: TokenData = verify_access_token(token)
    except HTTPException as e:
        raise

    data = new_password.dict(exclude_none=True)

    if "password" not in data:
        raise HTTPException(400, "No new password provided")

    data["password"] = get_password_hash(data["password"])
    
    update_result = await db["users"].update_one(
        {"_id": token_data.id},
        {"$set": {"password": data["password"]}}
    )
    user = await db['users'].find_one({"_id":token_data.id})

    if user:
        return user

    raise HTTPException(404, "User not found")
