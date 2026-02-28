import os
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.document import Document
from app.db.models.project import Project
from app.schemas import DocumentOut
from app.auth import get_current_user

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])

DATA_ROOT = Path("/data")  # volume do docker-compose

@router.post("", response_model=DocumentOut)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    # folder: /data/projects/{id}/docs
    target_dir = DATA_ROOT / "projects" / str(project_id) / "docs"
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = os.path.basename(file.filename)
    target_path = target_dir / safe_name

    content = await file.read()
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
def list_documents(project_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
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