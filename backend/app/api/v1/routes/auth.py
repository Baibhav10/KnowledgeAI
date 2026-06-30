"""
Signup and login endpoints.
Signup creates a new Organization + User in one transaction — if either
fails, both roll back, so we never end up with an orphaned Organization
with no User.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse

router = APIRouter()

from app.api.v1.dependencies import get_current_user
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    organization = Organization(name=payload.organization_name)
    db.add(organization)
    db.flush()  # assigns organization.id without committing yet

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        organization_id=organization.id,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    db.refresh(user)
    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        organization_id=str(current_user.organization_id),
    )