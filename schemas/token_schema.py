# Nhiệm vụ : Định dạng response trả về khi login thành công (token), 
# Và cấu trúc dữ liệu bên trong payload jwt sau khi decode (TokenPayload)

from typing import Optional 
from pydantic import BaseModel 

class Token(BaseModel):
    access_token:str 
    token_type:str = "bearer"
    


class TokenPayload(BaseModel):
    sub:Optional[str]=None 

