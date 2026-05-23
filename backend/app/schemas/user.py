from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class UserCreate:
    email: str
    password: str
    nickname: str

@dataclass
class UserLogin:
    email: str
    password: str

@dataclass
class UserResponse:
    id: str
    email: str
    nickname: str
    created_at: datetime
    last_login: Optional[datetime]

@dataclass
class Token:
    access_token: str
    token_type: str

@dataclass
class TokenData:
    user_id: Optional[str] = None