from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db.database import get_db
from app.db.models.project import Project
from app.db.models.document import Document
from app.db.models.user import User
from app.services.indexer import index_document
from app.services.lmstudio_client import embed_text
from app.services.qdrant_store import search as qdrant_search

router = APIRouter(prefix="/projects/{project_id}/rag", tags=["rag"])


class SearchReq(BaseModel):
    query: str = Field(min_length=2)
    top_k: int = Field(default=5, ge=1, le=20)
    doc_id: int | None = None


def _project_or_404(db: Session, project_id: int, owner: User) -> Project:
    p = db.query(Project).filter(Project.id == project_id, Project.owner_id == owner.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.post("/index")
def index_all(
    project_id: int,
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_user),
):
    _project_or_404(db, project_id, owner)

    docs = db.query(Document).filter(Document.project_id == project_id).all()
    if not docs:
        return {"indexed": 0, "details": []}

    details = []
    for d in docs:
        try:
            result = index_document(
                project_id=project_id,
                doc_id=d.id,
                filename=d.filename,
                storage_path=d.storage_path,
            )
            if "chunks" in result and result["chunks"] > 0:
                d.status = "indexed"
            else:
                d.status = "empty"
        except Exception as e:
            result = {"doc_id": d.id, "chunks": 0, "error": str(e)}
            d.status = "error"
        db.add(d)
        details.append(result)

    db.commit()
    return {"indexed": sum(1 for x in details if x.get("chunks", 0) > 0), "details": details}


@router.post("/search")
def search(
    project_id: int,
    req: SearchReq,
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_user),
):
    _project_or_404(db, project_id, owner)

    qvec = embed_text([req.query])[0]
    results = qdrant_search(project_id, qvec, top_k=req.top_k, doc_id=req.doc_id)

    return {
        "query": req.query,
        "top_k": req.top_k,
        "results": [
            {
                "score": r.score,
                "doc_id": r.doc_id,
                "chunk_id": r.chunk_id,
                "text": r.text,
                "filename": r.filename,
                "storage_path": r.storage_path,
            }
            for r in results
        ],
    }