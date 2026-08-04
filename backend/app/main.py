from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.api.v1.router import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Diamond Selling Intelligence API...")
    yield
    logger.info("Shutting down API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Real-time AI Diamond Selling Intelligence Platform - Polars Parquet Engine",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "status": "ok",
        "name": settings.PROJECT_NAME,
        "engine": "Polars Parquet Storage Engine",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
