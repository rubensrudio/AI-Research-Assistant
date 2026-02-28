from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="")