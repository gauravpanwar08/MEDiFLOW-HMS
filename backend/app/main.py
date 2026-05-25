from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger

# Import all routers
from app.domains.appointments.router import router as appointments_router
from app.domains.queues.router import router as queues_router
from app.domains.attendance.router import router as attendance_router
from app.domains.auth.router import router as auth_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Production-ready Hospital Management System",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- GLOBAL EXCEPTION HANDLERS ---
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handles our custom business logic exceptions"""
        logger.error(f"AppException: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.message, "data": None},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Overrides default FastAPI HTTP exceptions (e.g., 404 Not Found)"""
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": str(exc.detail), "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Overrides Pydantic validation errors (e.g., missing fields)"""
        # Format the ugly pydantic error into a readable string
        errors = [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"success": False, "message": "Validation Error", "data": errors},
        )

    # --- ROUTER REGISTRATION ---
    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(appointments_router, prefix=settings.API_V1_STR)
    app.include_router(queues_router, prefix=settings.API_V1_STR)
    app.include_router(attendance_router, prefix=settings.API_V1_STR)

    return app

app = create_app()
