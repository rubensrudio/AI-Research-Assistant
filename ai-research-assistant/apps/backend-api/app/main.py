from fastapi import FastAPI
from app.db.models.base import Base
from app.db.database import engine
from app.api.routes.health import router as health_router

def create_app() -> FastAPI:
    app = FastAPI(title="AI Research Assistant API", version="0.1.0")

    @app.on_event("startup")
    def _startup():
        Base.metadata.create_all(bind=engine)

    app.include_router(health_router)

    @app.get("/")
    def root():
        return {"name": "AI Research Assistant API", "status": "running"}

    return app

app = create_app()