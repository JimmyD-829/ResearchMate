from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..schemas.follow import FollowCreate, FollowResponse
from ..schemas.news import NewsListResponse
from ..services.follow_service import FollowService
from ..services.news_service import NewsService
from ..database import get_db

router = APIRouter(prefix="/api", tags=["news"])

class FetchNewsRequest(BaseModel):
    companies: List[str]

@router.post("/news/fetch")
async def fetch_news_for_companies(
    request: FetchNewsRequest,
    db: Session = Depends(get_db)
):
    fetched_count = 0
    results = []

    for company in request.companies:
        try:
            articles = NewsService.fetch_news_from_api([company])
            for article_data in articles:
                article = NewsService.create_news_article(db, article_data)
                results.append({
                    "company": company,
                    "title": article_data["title"],
                    "status": "success"
                })
                fetched_count += 1
        except Exception as e:
            results.append({
                "company": company,
                "error": str(e),
                "status": "failed"
            })

    return {
        "success": True,
        "fetched": fetched_count,
        "results": results,
        "message": f"Successfully fetched {fetched_count} news articles"
    }

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

        if total == 0:
            from ..utils.news_generator import NewsGenerator
            generated_news = NewsGenerator.generate_news(company_name, limit)

            for news_item in generated_news:
                try:
                    NewsService.create_news_article_from_dict(db, news_item)
                except:
                    pass

            items = generated_news
            total = len(generated_news)
    else:
        followed_companies = FollowService.get_user_followed_companies(db, current_user["id"])
        if followed_companies:
            total = NewsService.count_news(db)
            items = NewsService.get_news_for_companies(db, followed_companies, limit, offset)

            all_items_with_generated = list(items)

            for company in followed_companies:
                company_news_count = sum(1 for item in items if item.company_name == company)
                if company_news_count == 0:
                    from ..utils.news_generator import NewsGenerator
                    generated = NewsGenerator.generate_news(company, 10)
                    all_items_with_generated.extend(generated)

                    for news_item in generated:
                        try:
                            NewsService.create_news_article_from_dict(db, news_item)
                        except:
                            pass

            all_items_with_generated.sort(key=lambda x: x.publish_time if hasattr(x, 'publish_time') else '', reverse=True)
            items = all_items_with_generated[:limit]
            total = len(all_items_with_generated)
        else:
            total = NewsService.count_news(db)
            items = NewsService.get_all_news(db, limit, offset)

    return {"total": total, "items": items}

@router.post("/news/update")
async def update_news_daily(db: Session = Depends(get_db)):
    from ..services.news_scheduler import NewsScheduler
    result = NewsScheduler.daily_news_update()
    return result

@router.post("/news/force-update")
async def force_update_news(db: Session = Depends(get_db)):
    from ..services.news_scheduler import NewsScheduler
    result = NewsScheduler.force_update_all()
    return result
