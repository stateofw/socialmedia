from fastapi import APIRouter
from app.api.routes import auth, clients, content, users, intake, webhook, approval, analytics, admin, client_portal, upload

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(intake.router, prefix="/intake", tags=["intake"])
api_router.include_router(upload.router, tags=["upload"])  # No prefix - serves /upload and /media
api_router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
api_router.include_router(approval.router, prefix="/approval", tags=["approval"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(client_portal.router, prefix="/client", tags=["client-portal"])
