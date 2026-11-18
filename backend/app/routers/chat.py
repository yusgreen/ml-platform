"""Chat router."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import CHAT_RATE_LIMIT, CHAT_RATE_WINDOW
from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services import llm_service
from app.services.rate_limiter import check_rate_limit

router = APIRouter(prefix="/api/chat", tags=["chat"])

RATE_LIMIT_MESSAGES = {
    "es": "Demasiadas preguntas seguidas. Espera un minuto e intenta de nuevo.",
    "en": "Too many questions in a row. Wait a minute and try again.",
}


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, request: Request, db: Session = Depends(get_db)):
    lang = (req.lang or "es").lower()
    if lang not in ("es", "en"):
        lang = "es"

    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip, CHAT_RATE_LIMIT, CHAT_RATE_WINDOW):
        raise HTTPException(status_code=429, detail=RATE_LIMIT_MESSAGES[lang])

    try:
        reply = llm_service.chat(req.dataset_id, req.message, req.history, lang)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ChatResponse(reply=reply)
