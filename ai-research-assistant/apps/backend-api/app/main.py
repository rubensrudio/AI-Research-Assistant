from fastapi import FastAPI
from app.database import Base, engine
from app.core.vector_store import create_collection

app = FastAPI()

Base.metadata.create_all(bind=engine)
create_collection()

@app.get("/")
def root():
    return {"status": "running"}