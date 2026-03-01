from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserOut(BaseModel):
    id: int
    email: EmailStr

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: Optional[str] = ""

class ProjectOut(BaseModel):
    id: int
    name: str
    description: str

class DocumentOut(BaseModel):
    id: int
    project_id: int
    filename: str
    storage_path: str
    status: str