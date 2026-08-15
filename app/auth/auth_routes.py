from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth.security import(
    create_access_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("login")
async def login(data: LoginRequest):

    # temporary hardcoded credentials
    if data.username != "admin":
        raise HTTPException(
            status_code = 401, 
            detail = "Invalid username"
        )
    
    if data.password != "admin":
        raise HTTPException(
            status_code = 401,
            detail = "Invalid password"
        )


    token = create_access_token(
        {"sub": data.username}
    )

    return{
        "access_token": token,
        "token_type": "bearer"
    }
    