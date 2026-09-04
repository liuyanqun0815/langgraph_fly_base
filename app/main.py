from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.middleware.trace_id import TraceIdMiddleware
from app.routers import chat
from config import app_secret_key
from sale_app.core.mutil.flow_graph import shutdown_chain, startup_chain

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_chain()
    yield
    shutdown_chain()


app = FastAPI(title="langgraph_fly_base", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=app_secret_key())
app.add_middleware(TraceIdMiddleware)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(chat.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
