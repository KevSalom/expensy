import json
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import (
    Mode,
    create_access_token,
    get_current_user,
    require_demo_user,
    require_personal_user,
)
from airtable_rest import list_records as airtable_list_records
from config import settings
from supervisor import stream_supervisor_events
from users import verify_demo_password, verify_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Expensy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    name: str | None = None
    password: str | None = Field(default=None)
    mode: Mode


class LoginResponse(BaseModel):
    token: str
    name: str | None
    mode: Mode
    expires_at: str


class MeResponse(BaseModel):
    name: str | None
    mode: Mode
    expires_at: str


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Incoming request: %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info(
        "Response: %s for %s %s",
        response.status_code,
        request.method,
        request.url.path,
    )
    return response


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Expensy"}


def ui_message_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def datetime_from_exp(exp: int | None) -> str:
    if not exp:
        return ""
    return datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()


async def generate_ui_stream(message: str, mode: Mode) -> AsyncIterator[str]:
    message_id = f"msg_{uuid.uuid4().hex}"
    text_id = f"text_{uuid.uuid4().hex}"

    yield ui_message_event({"type": "start", "messageId": message_id})
    yield ui_message_event({"type": "text-start", "id": text_id})
    yield ui_message_event({"type": "data-progress", "data": {"messageId": message_id, "text": "Analizando tu solicitud..."}})
    yield ui_message_event({"type": "data-progress", "data": {"messageId": message_id, "text": "Expensy trabajando..."}})

    try:
        async for event in stream_supervisor_events(message=message, mode=mode):
            if event["type"] == "progress":
                yield ui_message_event({"type": "data-progress", "data": {"messageId": message_id, "text": event["text"]}})
            elif event["type"] == "final":
                yield ui_message_event(
                    {"type": "text-delta", "id": text_id, "delta": event["text"]}
                )
    except Exception:
        logger.exception("Expensy stream failed for mode=%s", mode)
        yield ui_message_event(
            {
                "type": "text-delta",
                "id": text_id,
                "delta": (
                    "No pude completar la accion por un error tecnico. "
                    "Revisa la configuracion de Airtable/OpenAI y vuelve a intentar."
                ),
            }
        )
    finally:
        yield ui_message_event({"type": "text-end", "id": text_id})
        yield ui_message_event({"type": "finish"})


def chat_stream_response(message: str, mode: Mode) -> StreamingResponse:
    return StreamingResponse(
        generate_ui_stream(message=message, mode=mode),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "x-vercel-ai-ui-message-stream": "v1",
        },
    )


@app.post("/api/auth/login", response_model=LoginResponse)
async def auth_login(payload: LoginRequest) -> LoginResponse:
    name = (payload.name or "").strip() or None
    password = payload.password

    if payload.mode == "personal":
        if not name:
            raise HTTPException(status_code=422, detail="Nombre requerido")
        if not password:
            raise HTTPException(status_code=422, detail="Contraseña requerida")
        if not verify_user(name=name, password=password):
            raise HTTPException(status_code=401, detail="Credenciales invalidas")
    else:
        # En modo demo ya no se requiere verificar contraseña
        pass

    token, expires_at = create_access_token(name=name, mode=payload.mode)
    return LoginResponse(
        token=token,
        name=name if payload.mode == "personal" else None,
        mode=payload.mode,
        expires_at=expires_at.isoformat(),
    )


@app.post("/api/auth/logout")
async def auth_logout() -> dict:
    # Stateless JWT: the client simply discards the token. Endpoint kept
    # for symmetry with /login and future server-side revocation needs.
    return {"ok": True}


@app.get("/api/auth/me", response_model=MeResponse)
async def auth_me(payload: dict = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        name=payload.get("name"),
        mode=payload.get("mode"),
        expires_at=datetime_from_exp(payload.get("exp")),
    )


@app.post("/api/chat/personal/stream")
async def personal_chat_stream(
    payload: ChatRequest,
    _user: dict = Depends(require_personal_user),
):
    return chat_stream_response(message=payload.message.strip(), mode="personal")


@app.post("/api/chat/demo/stream")
async def demo_chat_stream(
    payload: ChatRequest,
    _user: dict = Depends(require_demo_user),
):
    return chat_stream_response(message=payload.message.strip(), mode="demo")


@app.get("/api/warmup")
def warmup():
    """Warmup endpoint to keep Airtable connection active by requesting the last record."""
    results = {}
    
    # Warm up personal base
    try:
        personal_records = airtable_list_records(
            mode="personal",
            table_id=settings.airtable_expenses_table_id,
            sort=[{"field": "Fecha de Gasto", "direction": "desc"}],
            max_records=1,
        )
        results["personal"] = {
            "status": "success",
            "record_count": len(personal_records),
            "last_record": personal_records[0] if personal_records else None,
        }
    except Exception as e:
        logger.error("Warmup failed for personal Airtable: %s", e)
        results["personal"] = {"status": "error", "error": str(e)}
        
    # Warm up demo base
    try:
        demo_records = airtable_list_records(
            mode="demo",
            table_id=settings.airtable_expenses_table_id,
            sort=[{"field": "Fecha de Gasto", "direction": "desc"}],
            max_records=1,
        )
        results["demo"] = {
            "status": "success",
            "record_count": len(demo_records),
            "last_record": demo_records[0] if demo_records else None,
        }
    except Exception as e:
        logger.error("Warmup failed for demo Airtable: %s", e)
        results["demo"] = {"status": "error", "error": str(e)}
        
    return {"status": "ok", "results": results}
