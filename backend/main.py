import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import Settings, settings
from supervisor import stream_supervisor_events

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

Mode = Literal["personal", "demo"]

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


def get_settings() -> Settings:
    return settings


async def verify_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
    config: Settings = Depends(get_settings),
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    return authorization.removeprefix("Bearer ").strip()


def assert_token_for_mode(token: str, mode: Mode, config: Settings) -> None:
    expected_token = (
        config.personal_api_token if mode == "personal" else config.demo_api_token
    )
    if token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid bearer token")


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


async def generate_ui_stream(message: str, mode: Mode) -> AsyncIterator[str]:
    message_id = f"msg_{uuid.uuid4().hex}"
    text_id = f"text_{uuid.uuid4().hex}"
    
    initial_progress = "💭 Analizando tu solicitud..."
    progress_shown = False

    yield ui_message_event({"type": "start", "messageId": message_id})
    yield ui_message_event({"type": "text-start", "id": text_id})

    try:
        async for event in stream_supervisor_events(message=message, mode=mode):
            if event["type"] == "progress":
                if not progress_shown:
                    progress_shown = True
                    yield ui_message_event({"type": "data-progress", "data": {"text": initial_progress}})
                yield ui_message_event({"type": "data-progress", "data": {"text": event["text"]}})
            elif event["type"] == "final":
                if not progress_shown:
                    progress_shown = True
                    yield ui_message_event({"type": "data-progress", "data": {"text": initial_progress}})
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
                    "Revisa la configuracion de Airtable MCP/OpenAI y vuelve a intentar."
                ),
            }
        )
    finally:
        yield ui_message_event({"type": "text-end", "id": text_id})
        yield ui_message_event({"type": "finish"})


async def chat_stream(
    payload: ChatRequest,
    mode: Mode,
    token: str,
    config: Settings,
) -> StreamingResponse:
    assert_token_for_mode(token=token, mode=mode, config=config)

    return StreamingResponse(
        generate_ui_stream(message=payload.message.strip(), mode=mode),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "x-vercel-ai-ui-message-stream": "v1",
        },
    )


@app.post("/api/chat/personal/stream")
async def personal_chat_stream(
    payload: ChatRequest,
    token: str = Depends(verify_bearer_token),
    config: Settings = Depends(get_settings),
):
    return await chat_stream(payload=payload, mode="personal", token=token, config=config)


@app.post("/api/chat/demo/stream")
async def demo_chat_stream(
    payload: ChatRequest,
    token: str = Depends(verify_bearer_token),
    config: Settings = Depends(get_settings),
):
    return await chat_stream(payload=payload, mode="demo", token=token, config=config)
