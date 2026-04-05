from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.models.base import Base
from app.db.database import engine
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.documents import router as documents_router
from app.api.routes.llm_smoke import router as llm_router
from app.api.routes.rag import router as rag_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _backfill_project_owner_id()
    yield


def _backfill_project_owner_id():
    """Add owner_id column to projects table if missing, backfill from first user."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return
    col_names = {col["name"] for col in inspector.get_columns("projects")}
    if "owner_id" in col_names:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE projects ADD COLUMN owner_id INTEGER"))
        conn.execute(text(
            "UPDATE projects SET owner_id = (SELECT MIN(id) FROM users) "
            "WHERE owner_id IS NULL AND (SELECT COUNT(*) FROM users) > 0"
        ))


def create_app() -> FastAPI:
    app = FastAPI(title="AI Research Assistant API", version="0.1.0", lifespan=lifespan)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(documents_router)
    app.include_router(llm_router)
    app.include_router(rag_router)

    @app.get("/")
    def root():
        return {"name": "AI Research Assistant API", "status": "running"}

    return app

app = create_app()