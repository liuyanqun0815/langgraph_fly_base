import asyncio

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.middleware.session_csrf import get_csrf_token, validate_csrf
from app.templates_env import templates
from sale_app.core.handle_core import flow_control
from sale_app.util.UUIDUtils import generate_random_string

router = APIRouter()


def _serialize_messages(messages):
    rows = []
    for msg in messages:
        msg_type = getattr(msg, "type", None) or msg.__class__.__name__.lower()
        if "human" in msg_type:
            rows.append({"type": "human", "content": msg.content})
        elif "ai" in msg_type:
            rows.append({"type": "ai", "content": msg.content})
    return rows


@router.get("/api/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    csrf_token = get_csrf_token(request)
    return templates.TemplateResponse(
        request,
        "chat.html",
        {
            "csrf_token": csrf_token,
            "session_id": "",
            "chat": "",
            "data": None,
            "message": "",
        },
    )


@router.post("/api/chat", response_class=HTMLResponse)
async def chat_submit(
    request: Request,
    chat: str = Form(...),
    sessionId: str = Form(""),
    csrfmiddlewaretoken: str = Form(None),
):
    if not validate_csrf(request, csrfmiddlewaretoken):
        raise HTTPException(status_code=403, detail="CSRF validation failed")

    session_id = sessionId or generate_random_string(11)
    data = await asyncio.to_thread(flow_control, chat, session_id)
    return templates.TemplateResponse(
        request,
        "chat.html",
        {
            "csrf_token": get_csrf_token(request),
            "session_id": session_id,
            "chat": "",
            "data": _serialize_messages(data),
            "message": "执行成功",
        },
    )
