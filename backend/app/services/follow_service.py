from sqlalchemy.orm import Session
from ..models.follow import UserFollow
from ..schemas.follow import FollowCreate

class FollowService:
    @staticmethod
    def create_follow(db: Session, user_id: str, follow_data: FollowCreate) -> UserFollow:
        follow = UserFollow(
            user_id=user_id,
            company_name=follow_data.company_name,
            stock_code=follow_data.stock_code
        )
        db.add(follow)
        db.commit()
        db.refresh(follow)
        return follow
    
    @staticmethod
    def get_user_follows(db: Session, user_id: str) -> list:
        return db.query(UserFollow).filter(UserFollow.user_id == user_id).all()
    
    @staticmethod
    def get_follow_by_id(db: Session, follow_id: str) -> UserFollow:
        return db.query(UserFollow).filter(UserFollow.id == follow_id).first()
    
    @staticmethod
    def delete_follow(db: Session, follow_id: str) -> bool:
        follow = FollowService.get_follow_by_id(db, follow_id)
        if follow:
            db.delete(follow)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_user_followed_companies(db: Session, user_id: str) -> list:
        follows = FollowService.get_user_follows(db, user_id)
        return [follow.company_name for follow in follows]
