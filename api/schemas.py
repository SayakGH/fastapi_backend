from dotenv import load_dotenv
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr
from pydantic import GetCoreSchemaHandler
import motor.motor_asyncio
import os

load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))

db = client.blog_api

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        # Use Pydantic v2 core schema hook for validation
        return handler.wrap_validator_function(cls.validate)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_, handler):
        # Describe as string in OpenAPI
        return {"type": "string", "format": "object-id"}

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return ObjectId(v)


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
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
