import secrets

from starlette.requests import Request


def get_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def validate_csrf(request: Request, form_token: str | None) -> bool:
    session_token = request.session.get("csrf_token")
    if not session_token or not form_token:
        return False
    return secrets.compare_digest(session_token, form_token)
