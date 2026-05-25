from fastapi import APIRouter
from app.api.v1.endpoints import auth, doctors, patients, appointments, records, misc

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(doctors.router)
api_router.include_router(patients.router)
api_router.include_router(appointments.router)
api_router.include_router(records.router)
api_router.include_router(misc.analytics_router)
api_router.include_router(misc.ai_router)
api_router.include_router(misc.notifications_router)
api_router.include_router(misc.audit_router)
api_router.include_router(misc.hospitals_router)
api_router.include_router(misc.ws_router)
