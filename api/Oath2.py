import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()


def create_access_token(payload: dict):
    to_encode = payload.copy()

    expiration_time = datetime.utcnow() + timedelta()
    to_encode.update({"exp": expiration_time})
    jwt_token = jwt.encode(to_encode,os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM", "HS256"))
    return jwt_token