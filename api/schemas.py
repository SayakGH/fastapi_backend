import os
from typing import Optional
from dotenv import load_dotenv
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr
from pydantic_core import core_schema
import motor.motor_asyncio

# Load environment variables
load_dotenv()

# Initialize MongoDB client and select database
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client.blog_api

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler) -> core_schema.CoreSchema:
        """
        Hook into Pydantic v2 to validate incoming data as a string and
        convert it to a BSON ObjectId.
        """
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            json_schema_input_schema=core_schema.str_schema()
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_, handler) -> dict:
        """
        Provide a fixed JSON schema representation for OpenAPI,
        so Pydantic doesn’t try to derive it from the validator.
        """
        return {"type": "string", "format": "object-id"}

    @classmethod
    def validate(cls, v):
        """
        Ensure the value is a valid ObjectId string, then return
        the corresponding ObjectId instance.
        """
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return ObjectId(v)


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)

    model_config = {
        "populate_by_name": True,         # allow using alias="_id"
        "arbitrary_types_allowed": True,  # permit PyObjectId
        "json_encoders": {ObjectId: str}, # serialize ObjectId to string
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "jdoe@example.com",
                "password": "password123"
            }
        }
    }


class UserResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    email: EmailStr = Field(...)
    verified: Optional[bool] = Field(default=False)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "jdoe@example.com"
            }
        }
    }

class BlogContent(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str = Field(...)
    body: str = Field(...)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "blog title",
                "body": "blog content",
                "auther_name": "name of the auther",
                "auther_id": "ID of the auther",
                "created_at": "Date of blog creation"
            }
        }


class BlogContentResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str = Field(...)
    body: str = Field(...)
    author_name: str = Field(...)
    author_id: str = Field(...)
    created_at: str = Field(...)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "blog title",
                "body": "blog content",
                "auther_name": "name of the auther",
                "auther_id": "ID of the auther",
                "created_at": "Date of blog creation"
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(...)


class PasswordReset(BaseModel):
    password: str = Field(...)

class OtpVerification(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code as string")
    user_id: str = Field(...)

class OtpRequest(BaseModel):
    otp: int = Field(..., ge=100000, le=999999, description="6-digit OTP code")

class OtpResponse(BaseModel):
    message: str = Field(..., description="Response message indicating success or failure of OTP verification")