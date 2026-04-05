import os
import re
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.document import Document
from app.db.models.project import Project
from app.db.models.user import User
from app.schemas import DocumentOut
from app.auth import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
    "text/csv",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _safe_filename(name: str) -> str:
    name = os.path.basename(name)
    name = re.sub(r"[^\w\.\- ]", "_", name)
    name = re.sub(r"\.+[./\\]", ".", name)
    name = name.lstrip(".")
    if not name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name


def _project_or_404(db: Session, project_id: int, owner: User) -> Project:
    p = db.query(Project).filter(Project.id == project_id, Project.owner_id == owner.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.post("", response_model=DocumentOut)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_user),
):
    _project_or_404(db, project_id, owner)

    # Validate content type
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    safe_name = _safe_filename(file.filename or "untitled")
    target_dir = Path(settings.data_root) / "projects" / str(project_id) / "docs"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # Prevent overwriting
    if target_path.exists():
        raise HTTPException(status_code=409, detail="A file with this name already exists")

    target_path.write_bytes(content)

    doc = Document(
        project_id=project_id,
        filename=safe_name,
        storage_path=str(target_path),
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return DocumentOut(
        id=doc.id,
        project_id=doc.project_id,
        filename=doc.filename,
        storage_path=doc.storage_path,
        status=doc.status,
    )


@router.get("", response_model=list[DocumentOut])
def list_documents(
    project_id: int,
    db: Session = Depends(get_db),
    owner: User = Depends(get_current_user),
):
    _project_or_404(db, project_id, owner)
    rows = db.query(Document).filter(Document.project_id == project_id).order_by(Document.id.desc()).all()
    return [
        DocumentOut(
            id=d.id,
            project_id=d.project_id,
            filename=d.filename,
            storage_path=d.storage_path,
            status=d.status,
        )
        for d in rows
    ]