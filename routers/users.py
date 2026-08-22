from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User
from schemas.user import UserResponse
from dependencies.auth import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=List[UserResponse])
def list_users(
    search: Optional[str] = Query(None, description="Tìm theo email hoặc họ tên"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái tài khoản"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = db.query(User)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(or_(User.email.ilike(like_pattern), User.full_name.ilike(like_pattern)))

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.all()