from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..schemas.follow import FollowCreate, FollowResponse
from ..schemas.news import NewsListResponse
from ..services.follow_service import FollowService
from ..services.news_service import NewsService
from ..database import get_db

router = APIRouter(prefix="/api", tags=["news"])

@router.post("/follows", response_model=FollowResponse, status_code=status.HTTP_201_CREATED)
def follow_company(
    follow_data: FollowCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    return FollowService.create_follow(db, current_user["id"], follow_data)

@router.get("/follows", response_model=list[FollowResponse])
def get_follows(
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    return FollowService.get_user_follows(db, current_user["id"])

@router.delete("/follows/{follow_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_company(follow_id: str, db: Session = Depends(get_db)):
    success = FollowService.delete_follow(db, follow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Follow not found")

@router.get("/news", response_model=NewsListResponse)
def get_news(
    company_name: str = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    if company_name:
        total = NewsService.count_news(db, company_name)
        items = NewsService.get_news_by_company(db, company_name, limit, offset)
    else:
        followed_companies = FollowService.get_user_followed_companies(db, current_user["id"])
        if followed_companies:
            total = NewsService.count_news(db)
            items = NewsService.get_news_for_companies(db, followed_companies, limit, offset)
        else:
            total = NewsService.count_news(db)
            items = NewsService.get_all_news(db, limit, offset)
    
    return {"total": total, "items": items}
