from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from ..schemas import db, TokenData, OtpRequest, OtpResponse,OtpVerification
from ..Oauth2 import get_current_user
from ..utils import otp_gen
from ..send_mail import send_verification_otp

router= APIRouter(
    prefix='/otp'
    , tags=["OTP Verification"]
)

@router.get("", response_description="Generate OTP")
async def generate_otp(current_user: TokenData = Depends(get_current_user)):
    try:
        otp_code = otp_gen()
        otp_doc = {"otp": otp_code, "user_id": current_user.id}

        result = await db["otp"].insert_one(otp_doc)

        user = await db["users"].find_one({"_id": current_user.id})
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        await send_verification_otp(
            subject="OTP VERIFICATION",
            email_to=user["email"],
            body={
                "title": "Password Reset OTP",
                "name": user["name"],
                "otp": otp_code
            }
        )
        return {"msg": "OTP has been sent to your email"}
    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error in generate_otp:", repr(e))
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "",
    response_description="Verify OTP and mark user as verified"
)
async def verify_otp(
    payload: OtpRequest,
    current_user: TokenData = Depends(get_current_user)
):
    # turn into dict for clarity
    data = jsonable_encoder(payload)
    otp_code = data["otp"]
    user_id_str = current_user.id

    # DEBUG: print what we're about to query
    print(f"Looking up OTP record with user_id={user_id_str!r}, otp={otp_code!r}")

    # 1) Find the OTP record
    otp_record = await db["otp"].find_one({
    "user_id": user_id_str,
    "otp": str(otp_code)          # match the stored string
})
    print("OTP record found:", otp_record)

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    result = await db["users"].update_one(
        {"_id": current_user.id},
        {"$set": {"verified": True}}
    )
    print("User update result:", result.raw_result)

    if result.modified_count != 1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user verification status"
        )

    # 3) Clean up OTPs
    delete_count = (await db["otp"].delete_many({"user_id": user_id_str})).deleted_count
    print(f"Deleted {delete_count} OTP records for user")

    return {"msg": "User successfully verified"}