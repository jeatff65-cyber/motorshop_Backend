"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.base import Base, engine
from app.db.init_db import init_db  # seeds default admin (idempotent)

logger = logging.getLogger("uvicorn.error")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables at startup (idempotent).
    # For production, use Alembic migrations instead.
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database connection OK - tables ready.")
        # Seed the default admin account if the database is new/empty.
        try:
            init_db()
            logger.info("Admin account check done (admin@bookstore.com).")
        except Exception as exc:  # noqa: BLE001 - non-fatal
            logger.warning("Admin seed skipped: %s", exc)
    except Exception as exc:  # noqa: BLE001 - keep the server alive and warn clearly
        logger.error("Database connection FAILED: %s", exc)
        logger.error(
            "Fix it by editing the DATABASE_URL on Render / Backend/file.env:\n"
            "  1. Create a PostgreSQL database on Render if yours was deleted "
            "(free databases expire after 30 days).\n"
            "  2. Use the EXTERNAL Database URL from Render "
            "(Connections -> External Database URL), not the internal hostname.\n"
            "  3. Replace YOUR_DATABASE_PASSWORD with the real password.\n"
            "  OR for local testing only: set DATABASE_URL=sqlite:///./local.db"
        )
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Web platform for a Book Store - products, services, auth and admin dashboard.",
    lifespan=lifespan,
)

# CORS - allow the deployed frontends + local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Deployed frontends
        "https://bookstore-admin-zfwi.onrender.com",     # Admin dashboard
        "https://zippy-concha-47a6fd.netlify.app",       # Customer website (older Netlify deploy)
        "https://thyraa095-beep.github.io",              # Customer website (GitHub Pages)
        # Local development
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root() -> dict:
    return {
        "message": "Welcome to the Book Store API",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["Health"])
def health() -> dict:
    return {"status": "ok"}


