"""
Faculty Timetable Extraction System - FastAPI Entry Point
"""
import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.api.routes import auth, upload, preview, faculty, download, dashboard, export
from app.middleware.cors import setup_cors
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.error_handler import (
    global_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
)

# Setup basic logging before anything else
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise backend for Faculty Timetable Extraction System",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup Middleware
setup_cors(app)
app.add_middleware(LoggingMiddleware)

# Setup Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

# Include Routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(preview.router)
app.include_router(faculty.router)
app.include_router(download.router)
app.include_router(dashboard.router)
app.include_router(export.router)

from fastapi.staticfiles import StaticFiles
import os

# Create uploads dir if not exists
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/", tags=["Health"])
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

logger.info(f"Started {settings.APP_NAME} v{settings.APP_VERSION}")
