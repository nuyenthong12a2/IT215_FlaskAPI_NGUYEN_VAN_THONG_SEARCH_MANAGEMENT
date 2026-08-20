from datetime import datetime 
from typing import Optional 
from jose import jwt 
from passlib.context import CryptContext 
from core.config import settings 

pwd_context = CryptContext(schem)