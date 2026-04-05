from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.services.lmstudio_client import embed_text, chat

router = APIRouter(prefix="/llm", tags=["llm-smoke"])


class EmbedReq(BaseModel):
    texts: list[str]

class ChatReq(BaseModel):
    prompt: str

@router.post("/embed")
def test_embed(req: EmbedReq, _=Depends(get_current_user)):
    try:
        vectors = embed_text(req.texts)
        return {"count": len(vectors), "dim": len(vectors[0]) if vectors else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
def test_chat(req: ChatReq, _=Depends(get_current_user)):
    try:
        content = chat([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": req.prompt},
        ])
        return {"answer": content}
    except Exception:
        raise HTTPException(status_code=500, detail="Chat request failed")