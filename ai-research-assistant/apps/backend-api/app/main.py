from fastapi import FastAPI
from app.db.models.base import Base
from app.db.database import engine
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.documents import router as documents_router

def create_app() -> FastAPI:
    app = FastAPI(title="AI Research Assistant API", version="0.1.0")

    @app.on_event("startup")
    def _startup():
        Base.metadata.create_all(bind=engine)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(documents_router)

    @app.get("/")
    def root():
        return {"name": "AI Research Assistant API", "status": "running"}

    return app

app = create_app()