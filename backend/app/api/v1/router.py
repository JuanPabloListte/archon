from fastapi import APIRouter
from app.api.v1 import projects, connections, audits, reports, chat, dashboard
from app.api.v1 import auth

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(connections.router, prefix="/connections", tags=["connections"])
router.include_router(audits.router, prefix="/audits", tags=["audits"])
router.include_router(reports.router, prefix="/reports", tags=["reports"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
