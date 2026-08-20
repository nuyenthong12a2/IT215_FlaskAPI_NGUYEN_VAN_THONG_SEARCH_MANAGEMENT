from datetime import datetime,timedelta
from typing import Optional 
from jose import jwt 
from passlib.context import CryptContext 
from core.config import settings 

pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)->str:
    """ Băm mật khẩu 
    """    
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str)->bool:
    """ Kiểm tra mật khẩu nhập vào với mã băm 
    """    
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data:dict,expires_delta:Optional[timedelta]=None)->str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now.isoformat() + expires_delta 
    else:
        expire = datetime.now().isoformat(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
    
    