from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="ResearchMate API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://researchmate.pages.dev",
        "https://researchmate-aznu.onrender.com"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting ResearchMate API...")
    
    try:
        from app.database import engine, Base
        logger.info("Database module imported")
        
        from app.routes.auth import router as auth_router
        from app.routes.reports import router as reports_router
        from app.routes.news import router as news_router
        from app.routes.emotion import router as emotion_router
        from app.routes.analysis import router as analysis_router
        
        logger.info("All route modules imported")
        
        app.include_router(auth_router)
        app.include_router(reports_router)
        app.include_router(news_router)
        app.include_router(emotion_router)
        app.include_router(analysis_router)
        
        logger.info("All routers registered")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        logger.error(traceback.format_exc())
        raise

@app.get("/")
async def root():
    return {"message": "Welcome to ResearchMate API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}