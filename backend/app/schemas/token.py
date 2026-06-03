from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    # Optional so tokens issued before revocation support stay valid until expiry.
    jti: Optional[str] = None
    ver: Optional[int] = 0
    exp: Optional[int] = None
