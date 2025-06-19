import os
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

