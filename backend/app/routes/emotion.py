from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..schemas.emotion import EmotionScoreResponse, EmotionTrendResponse
from ..services.emotion_service import EmotionService
from ..database import get_db

router = APIRouter(prefix="/api/emotion", tags=["emotion"])

class UpdateEmotionRequest(BaseModel):
    company_name: str

@router.get("/{company_name}", response_model=EmotionScoreResponse)
def get_emotion_score(company_name: str, db: Session = Depends(get_db)):
    return EmotionService.get_emotion_score(db, company_name)

@router.get("/{company_name}/trend", response_model=EmotionTrendResponse)
def get_emotion_trend(
    company_name: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    return EmotionService.get_emotion_trend(db, company_name, days)

@router.post("/update")
def update_emotion_data(request: UpdateEmotionRequest, db: Session = Depends(get_db)):
    EmotionService.update_daily_emotion(db, request.company_name)
    return {"message": f"情绪数据已更新: {request.company_name}", "success": True}
