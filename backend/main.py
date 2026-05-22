from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from app.database import engine, Base
from app.routes.auth import router as auth_router
from app.routes.reports import router as reports_router
from app.routes.news import router as news_router
from app.routes.emotion import router as emotion_router
from app.routes.analysis import router as analysis_router

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ResearchMate API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(news_router)
app.include_router(emotion_router)
app.include_router(analysis_router)

@app.get("/")
async def root():
    return {"message": "Welcome to ResearchMate API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
