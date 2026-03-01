from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.project import Project
from app.schemas import ProjectCreate, ProjectOut
from app.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    proj = Project(name=payload.name, description=payload.description or "")
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return ProjectOut(id=proj.id, name=proj.name, description=proj.description)

@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(Project).order_by(Project.id.desc()).all()
    return [ProjectOut(id=p.id, name=p.name, description=p.description) for p in rows]

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(id=p.id, name=p.name, description=p.description)

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(p)
    db.commit()
    return {"deleted": True}