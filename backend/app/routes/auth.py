from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from ..schemas.user import UserCreate, UserLogin, UserResponse, Token
from ..services.user_service import UserService
from ..utils.auth import create_access_token, SECRET_KEY, ALGORITHM
from ..database import get_db
from jose import JWTError, jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])

def get_token(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    return token

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = UserService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = UserService.create_user(db, user_data)
    return user

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = UserService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    UserService.update_last_login(db, user.id)
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user(token: str = Depends(get_token), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = UserService.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user
