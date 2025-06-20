from fastapi import FastAPI
from .routes import users, auth, password_reset,blog_content, otp_verification


app = FastAPI()


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(password_reset.router)
app.include_router(blog_content.router)
app.include_router(otp_verification.router)

@app.get("/")
def get():
    return {"msg": "Hello World"}