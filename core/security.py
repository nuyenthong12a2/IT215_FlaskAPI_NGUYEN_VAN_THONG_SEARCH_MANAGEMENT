from datetime import datetime , timedelta,timezone 
from typing import Optional 

from jose import jwt 
from passlib.context import CryptContext 
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(plain_password:str)->str:
    """ Băm mật khẩu trước khi lưu vào DB
    """    
    return pwd_context.hash(plain_password)

def verify_password(plain_password:str,hashed_password:str)->bool:
    """ Kiểm tra mật khẩu đầu vào có đúng hay là không 
    """    
    return pwd_context.verify(plain_password,hashed_password)


def create_access_token(subject:str,expires_delta:Optional[timedelta]=None)->str:
    """
    Tạo jwt create token 
    sub : user.id -> ép user.id nằm trong payload
    expires_delta : Cho phép thời gian mặc định nếu cần (refresh token dùng thời gian dài)
    """    
    if expires_delta : 
        expire = datetime.now(timezone.utc) + expires_delta 
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    # "sub": subject là claim chuẩn dùng để định dạng chủ thể token 
    # "exp": quy định thời gian hết hạn - jwt.deocode() sẽ tự raise lỗi ExpiredSignatureError nếu token đã quá hạn khi decode 
    to_encode = {"sub":str(subject),"exp":expire}
    
    encoded_jwt = jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
    return encoded_jwt 

    