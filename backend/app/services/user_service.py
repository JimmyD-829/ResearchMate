from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserCreate
from ..utils.auth import verify_password, get_password_hash
from datetime import datetime

class UserService:
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            nickname=user_data.nickname
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = UserService.get_user_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def update_last_login(db: Session, user_id: str):
        user = UserService.get_user_by_id(db, user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.commit()
