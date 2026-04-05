from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.project import Project
from app.schemas import ProjectCreate, ProjectOut
from app.auth import get_current_user
from app.db.models.user import User

router = APIRouter(prefix="/projects", tags=["projects"])


def _get_project_or_404(db: Session, project_id: int, owner: User) -> Project:
    p = db.query(Project).filter(Project.id == project_id, Project.owner_id == owner.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p

@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), owner: User = Depends(get_current_user)):
    proj = Project(name=payload.name, description=payload.description or "", owner_id=owner.id)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return ProjectOut(id=proj.id, name=proj.name, description=proj.description)

@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), owner: User = Depends(get_current_user)):
    rows = db.query(Project).filter(Project.owner_id == owner.id).order_by(Project.id.desc()).all()
    return [ProjectOut(id=p.id, name=p.name, description=p.description) for p in rows]

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), owner: User = Depends(get_current_user)):
    p = _get_project_or_404(db, project_id, owner)
    return ProjectOut(id=p.id, name=p.name, description=p.description)

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), owner: User = Depends(get_current_user)):
    p = _get_project_or_404(db, project_id, owner)
    db.delete(p)
    db.commit()
    return {"deleted": True}