"""
MediCore HMS — FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.core.config import settings
from app.db.session import init_db, AsyncSessionLocal
from app.api.v1.router import api_router
import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MediCore HMS", version=settings.APP_VERSION)
    await init_db()
    await seed_default_hospital()
    yield
    # Shutdown
    logger.info("Shutting down")


async def seed_default_hospital():
    """Create default hospital if none exists."""
    from app.models.models import Hospital
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Hospital).where(Hospital.slug == settings.DEFAULT_HOSPITAL_SLUG))
        if not result.scalar_one_or_none():
            hospital = Hospital(
                name="City General Hospital",
                slug=settings.DEFAULT_HOSPITAL_SLUG,
                address="123 Medical Centre Road",
                phone="+91 22 1234 5678",
                email="admin@citygeneral.hospital",
                is_active=True,
                subscription_plan="enterprise",
            )
            db.add(hospital)
            await db.commit()
            logger.info("Default hospital created", slug=settings.DEFAULT_HOSPITAL_SLUG)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Hospital Management System",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})
