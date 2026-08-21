"""
FILE: routers/auth.py
VAI TRÒ: 2 endpoint công khai (không cần token) - đăng ký và đăng nhập.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User
from schemas.user import UserCreate, UserResponse
from schemas.token import Token
from core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Luồng:
      1. Check email đã tồn tại trong DB chưa -> nếu có, raise 400
         (raise ở đây, KHÔNG cần try/except IntegrityError, vì đã check
         trước khi insert nên sẽ không bao giờ chạm constraint UNIQUE ở DB)
      2. Hash password bằng hash_password() (KHÔNG BAO GIỜ lưu plain text)
      3. Tạo User mới với role mặc định "USER" (client KHÔNG được tự
         chọn role khi đăng ký - tránh tự phong ADMIN cho mình)
      4. commit + refresh để lấy lại id/created_at vừa được DB sinh ra
    """
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng",
        )

    new_user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        role="USER",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2PasswordRequestForm bắt buộc client gửi dữ liệu dạng
    application/x-www-form-urlencoded với 2 field "username" và "password"
    (đây là chuẩn OAuth2, KHÔNG phải JSON) - Swagger UI tự tạo form đúng
    định dạng này khi bấm nút "Authorize" hoặc "Try it out".
    form_data.username ở đây CHÍNH LÀ email (project không có username riêng).

    Luồng:
      1. Tìm user theo email -> không có, hoặc verify_password sai
         -> gộp chung 1 thông báo lỗi "Email hoặc mật khẩu không đúng"
         (KHÔNG nói rõ "email không tồn tại" hay "sai mật khẩu" riêng biệt
         -> tránh lộ thông tin email nào đã đăng ký trong hệ thống - đây là
         thông lệ bảo mật chuẩn, không phải thiếu sót)
      2. Check is_active -> nếu bị khóa, raise 403 (khác biệt rõ với 401:
         401 = chưa xác thực được / sai thông tin, 403 = đã xác thực đúng
         danh tính NHƯNG không có quyền truy cập)
      3. Tạo JWT access token, trả về theo schema Token
    """
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa",
        )

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer")