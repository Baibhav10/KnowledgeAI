"""
Pydantic schemas define the shape of data coming in and going out
of our API. FastAPI uses these to auto-validate requests and
auto-generate API docs.
"""
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    organization_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    organization_id: str

    class Config:
        from_attributes = True