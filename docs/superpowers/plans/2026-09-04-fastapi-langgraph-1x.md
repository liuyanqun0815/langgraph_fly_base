# FastAPI + LangGraph 1.x 升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `feat/project-optimization` 分支完成 Django → FastAPI 迁移，并将 LangGraph/LangChain 全栈升级到 1.x，SQLite checkpoint 使用 `langgraph-checkpoint-sqlite` 新 API。

**Architecture:** 保留 `sale_app/core/*` 业务与 LangGraph 图；新增 `app/` 作为 FastAPI 入口；Django ORM 换 SQLAlchemy 读现有 `db.sqlite3`；checkpoint 由 FastAPI lifespan 管理 `SqliteSaver` context。

**Tech Stack:** FastAPI、uvicorn、Jinja2、SQLAlchemy 2.0、langgraph 1.2.x、langchain-core 1.x、langgraph-checkpoint-sqlite、pytest、httpx TestClient

**Spec 来源:** `docs/superpowers/specs/2026-09-04-fastapi-langgraph-1x-design.md`

## Global Constraints

- 工作目录：优先使用 git worktree `E:/old_computer/PycharmProjects/langgraph_fly_base/.worktrees/project-optimization`，分支 `feat/project-optimization`
- Python **3.10 或 3.11**（3.13 可能因 numpy/依赖无解）；实施前用干净 venv 验证
- **不保留**旧 `storage/memory_file/chat_history.db` 格式；升级后文档要求删除重建
- **不重命名** `secrity` / `moudel` / `mutil` 目录
- KB 端点本阶段 **不要求** CSRF/鉴权（README 标注生产需加固）
- 每层/Task 结束必须 `pytest tests/ -v` 通过再进入下一 Task
- 代码：black `max_line_length=120`；`snake_case`；禁止 `from module import *`
- 每个 Task 独立 commit；失败时 `git revert` 单层

## 文件变更总览

| 路径 | 职责 |
|------|------|
| `requirements.txt` | 1.x + FastAPI 依赖窗，移除 Django |
| `app/main.py` | FastAPI 应用、lifespan、静态文件 |
| `app/middleware/trace_id.py` | TraceId ASGI 中间件 |
| `app/middleware/session_csrf.py` | Session + CSRF（聊天表单） |
| `app/routers/chat.py` | `/api/chat` |
| `app/routers/kb.py` | `/kb/*` |
| `app/routers/files.py` | `/file/image-preview/{file_name}` |
| `app/templates_env.py` | Jinja2 配置、csrf 模板函数 |
| `sale_app/core/mutil/flow_graph.py` | checkpoint 生命周期 + 1.x API |
| `sale_app/database/session.py` | SQLAlchemy engine/session |
| `sale_app/database/sqlalchemy_models.py` | Product、Datasets ORM |
| `sale_app/database/product.py` | 改用 SQLAlchemy 查询 |
| `config.py` | 增加 `DATABASE_URL`、`APP_SECRET_KEY`、路径常量 |
| `import_data_to_sqlite.py` | 去掉 Django，用 SQLAlchemy 导入 |
| `tests/test_imports_smoke.py` | 1.x 依赖烟测 |
| `tests/test_chat_csrf.py` | 改为 FastAPI TestClient |
| `README.md` | uvicorn 启动、删 checkpoint 说明 |

**L6 删除：** `manage.py`、`fly_base/`、`sale_app/chat_api/api.py`、`kb_api.py`、`file.py`、Django forms、`tests/test_urls.py`

---

## Task 1 (L1): 依赖窗升级到 LangGraph 1.x + FastAPI

**Files:**
- Modify: `requirements.txt`
- Modify: `.env.example`
- Create: `tests/test_imports_smoke.py`

**Interfaces:**
- Produces: 可 `pip install -r requirements.txt` 的 pin 集合；`langgraph.__version__` 以 `1.` 开头；`langchain_core` 以 `1.` 开头

- [ ] **Step 1: 备份当前 requirements**

```bash
cp requirements.txt requirements.phase-ac.txt.bak
```

- [ ] **Step 2: 重写 requirements.txt（基线，实施时用 pip 微调至可解析）**

```text
# Web
fastapi==0.115.6
uvicorn[standard]==0.32.1
python-multipart==0.0.20
jinja2==3.1.4
itsdangerous==2.2.0

# LangChain / LangGraph 1.x
langgraph==1.2.11
langgraph-checkpoint==4.1.0
langgraph-checkpoint-sqlite==2.0.11
langchain-core==1.6.1
langchain==1.3.16
langchain-openai==0.3.14
langchain-community==0.3.21
langchain-experimental==0.3.4

# 智谱 / 向量 / 文档
langchain-zhipu==4.1.8
langchain-milvus==0.2.1
pymilvus[model]==2.5.6
qdrant-client==1.12.2
langchain-qdrant==0.2.0
weaviate-client==3.26.7

# DB
sqlalchemy==2.0.36

# 业务依赖（保留 Phase A–C 版本或按兼容微调）
python-dotenv==1.0.1
langdetect==1.0.9
presidio-anonymizer==2.2.354
presidio-analyzer==2.2.354
Faker==25.8.0
pandas==2.2.3
openpyxl==3.1.5
python-docx==1.1.2
xlrd==2.0.1
unstructured[docx]==0.10.30

# 测试
pytest==8.3.2
httpx==0.28.1
pytest-asyncio==0.24.0
```

**注意：** 若 `langchain-milvus==0.2.1` 与 core 冲突，在 venv 中试装后调整；**移除** `Django`、`pytest-django`。

- [ ] **Step 3: 干净 venv 试装（Python 3.10）**

```powershell
python -m venv .venv-lg1
.\.venv-lg1\Scripts\activate
pip install -U pip
pip install -r requirements.txt
python -c "import langgraph, langchain_core; print(langgraph.__version__, langchain_core.__version__)"
```

Expected: `langgraph` 版本 `1.x`，`langchain_core` 版本 `1.x`，exit 0

- [ ] **Step 4: 写烟测（此时图/ Django 可能仍失败，只测包版本）**

Create `tests/test_imports_smoke.py`:

```python
def test_langgraph_is_1x():
    import langgraph

    assert langgraph.__version__.startswith("1.")


def test_langchain_core_is_1x():
    import langchain_core

    assert langchain_core.__version__.startswith("1.")


def test_fastapi_importable():
    import fastapi

    assert fastapi.__version__
```

- [ ] **Step 5: 更新 `.env.example`**

```dotenv
APP_SECRET_KEY=replace-me-for-session-csrf
DATABASE_URL=sqlite:///./db.sqlite3
# 保留现有 ZHIPU_*、VECTOR_TYPE、MILVUS_* 等
```

- [ ] **Step 6: 运行烟测并 commit**

```bash
pytest tests/test_imports_smoke.py -v
git add requirements.txt .env.example tests/test_imports_smoke.py
git commit -m "chore: upgrade deps to langgraph 1.x and add FastAPI stack"
```

---

## Task 2 (L2a): Pydantic v2 + 结构化输出适配

**Files:**
- Modify: `sale_app/secrity/pre_safety.py`
- Modify: `sale_app/core/mutil/fix_question.py`
- Modify: `sale_app/core/agent/intention_confirm.py`
- Modify: `sale_app/core/agent/information_gathering.py`
- Modify: `sale_app/core/agent/qa_handle.py`
- Test: `tests/test_field_defaults.py`（已有，需仍通过）

**Interfaces:**
- Consumes: langchain-core 1.x `with_structured_output`
- Produces: 全项目无 `langchain_core.pydantic_v1` 引用

- [ ] **Step 1: 全局替换 import**

每个文件：

```python
# 删除
from langchain_core.pydantic_v1 import BaseModel, Field

# 改为
from pydantic import BaseModel, Field
```

涉及文件见上 **Files** 列表；用 ripgrep 确认零残留：

```bash
rg "pydantic_v1" sale_app/
```

Expected: 无匹配

- [ ] **Step 2: 确认 Field 定义仍合法**

保持 Phase A–C 已修复的 `Field(default=None, ...)` 形式；若有 `model_config`，使用 Pydantic v2：

```python
class Classification(BaseModel):
    model_config = {"extra": "forbid"}
    isPublicSafety: int = Field(default=1, ...)
```

- [ ] **Step 3: 运行现有单测**

```bash
pytest tests/test_field_defaults.py tests/test_pre_safety.py -v
```

Expected: PASS（pre_safety 测试已有 mock 策略）

- [ ] **Step 4: Commit**

```bash
git commit -am "refactor: migrate structured output models to pydantic v2"
```

---

## Task 3 (L2b): LangGraph 1.x checkpoint 生命周期

**Files:**
- Modify: `sale_app/core/mutil/flow_graph.py`
- Modify: `sale_app/core/mutil/recommend_product_graph.py`（若 import 路径变化）
- Create: `tests/test_checkpoint_lifecycle.py`
- Modify: `README.md`（追加删除旧 db 说明，简短一行，L6 再完整更新）

**Interfaces:**
- Produces: `startup_chain()`、`shutdown_chain()`、`get_chain()`、`run_flow(question, config)` 签名不变
- Consumes: `langgraph.checkpoint.sqlite.SqliteSaver` context manager API

- [ ] **Step 1: 重构 flow_graph 模块级状态**

在 `sale_app/core/mutil/flow_graph.py` 末尾替换 checkpoint 逻辑：

```python
_chain = None
_checkpointer = None
_checkpointer_cm = None


def _checkpoint_db_path() -> str:
    from sale_app.util.file_utils import find_project_root

    db_path = (
        find_project_root(os.path.abspath(__file__))
        + "/storage/memory_file/chat_history.db"
    )
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path


def startup_chain() -> None:
    """在 FastAPI lifespan startup 调用；测试可跳过。"""
    global _chain, _checkpointer, _checkpointer_cm
    if _chain is not None:
        return
    from langgraph.checkpoint.sqlite import SqliteSaver

    from sale_app.core.moudel.zhipuai import ZhipuAI

    llm = ZhipuAI().openai_chat()
    graph = build_flow_graph(llm)
    _checkpointer_cm = SqliteSaver.from_conn_string(_checkpoint_db_path())
    _checkpointer = _checkpointer_cm.__enter__()
    _chain = graph.compile(checkpointer=_checkpointer)


def shutdown_chain() -> None:
    global _chain, _checkpointer, _checkpointer_cm
    if _checkpointer_cm is not None:
        _checkpointer_cm.__exit__(None, None, None)
    _checkpointer_cm = None
    _checkpointer = None
    _chain = None


def get_chain():
    global _chain
    if _chain is None:
        startup_chain()
    return _chain


def run_flow(question: str, config: dict) -> FlowState:
    return get_chain().invoke({"messages": [HumanMessage(content=question)]}, config)
```

**若 1.x API 要求 `async with` 或不同 import 路径**，以 venv 中实际包为准调整（常见为 `langgraph_checkpoint_sqlite`）。

- [ ] **Step 2: 写 checkpoint 烟测（不依赖真实 LLM）**

Create `tests/test_checkpoint_lifecycle.py`:

```python
from unittest.mock import MagicMock, patch


def test_startup_shutdown_resets_chain():
    import sale_app.core.mutil.flow_graph as fg

    fg.shutdown_chain()
    assert fg._chain is None

    mock_graph = MagicMock()
    mock_compiled = MagicMock()
    mock_graph.compile.return_value = mock_compiled

    with patch.object(fg, "build_flow_graph", return_value=mock_graph):
        with patch("sale_app.core.mutil.flow_graph.SqliteSaver") as mock_saver_cls:
            mock_cm = MagicMock()
            mock_checkpointer = MagicMock()
            mock_cm.__enter__.return_value = mock_checkpointer
            mock_saver_cls.from_conn_string.return_value = mock_cm

            fg.startup_chain()
            assert fg._chain is mock_compiled
            mock_graph.compile.assert_called_once_with(checkpointer=mock_checkpointer)

            fg.shutdown_chain()
            assert fg._chain is None
            mock_cm.__exit__.assert_called_once()
```

- [ ] **Step 3: 删除旧 checkpoint 文件（本地开发）**

```powershell
Remove-Item -Force storage/memory_file/chat_history.db -ErrorAction SilentlyContinue
```

- [ ] **Step 4: 运行图相关测试**

```bash
pytest tests/test_decide_router.py tests/test_flow_lazy_init.py tests/test_checkpoint_lifecycle.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sale_app/core/mutil/flow_graph.py tests/test_checkpoint_lifecycle.py
git commit -m "refactor: langgraph 1.x sqlite checkpoint lifecycle"
```

---

## Task 4 (L3): FastAPI 骨架 + TraceId + Session

**Files:**
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/middleware/trace_id.py`
- Create: `app/templates_env.py`
- Create: `tests/test_app_health.py`

**Interfaces:**
- Produces: `app.main:app` ASGI 应用；`GET /health` 返回 200

- [ ] **Step 1: TraceId 中间件（Starlette BaseHTTPMiddleware）**

Create `app/middleware/trace_id.py`:

```python
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from sale_app.util.traceId_log_handler import trace_id_var


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id_var.set(str(uuid.uuid4()).split("-")[-1])
        try:
            response = await call_next(request)
            return response
        finally:
            trace_id_var.set("N/A")
```

- [ ] **Step 2: Jinja2 环境**

Create `app/templates_env.py`:

```python
from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
```

- [ ] **Step 3: FastAPI main + lifespan**

Create `app/main.py`:

```python
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.middleware.trace_id import TraceIdMiddleware
from sale_app.core.mutil.flow_graph import shutdown_chain, startup_chain

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_chain()
    yield
    shutdown_chain()


app = FastAPI(title="langgraph_fly_base", lifespan=lifespan)
app.add_middleware(TraceIdMiddleware)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: 健康检查测试**

Create `tests/test_app_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 5: 运行测试**

```bash
pytest tests/test_app_health.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/ tests/test_app_health.py
git commit -m "feat: add FastAPI app skeleton with lifespan and trace middleware"
```

---

## Task 5 (L4a): 聊天路由 + CSRF + 模板适配

**Files:**
- Create: `app/middleware/session_csrf.py`
- Create: `app/routers/chat.py`
- Modify: `app/main.py`（注册 router、SessionMiddleware）
- Modify: `templates/chat.html`（Django 模板标签 → Jinja2）
- Modify: `config.py`（`APP_SECRET_KEY`）
- Replace: `tests/test_chat_csrf.py`
- Delete: `tests/test_urls.py`（Django 专用）

**Interfaces:**
- Produces: `GET/POST /api/chat`；POST 无 CSRF → 403；有 token → 200
- Consumes: `sale_app.core.handle_core.flow_control`

- [ ] **Step 1: config.py 增加 APP_SECRET_KEY**

```python
DEFAULTS = {
    # ...existing...
    'APP_SECRET_KEY': 'dev-only-change-me',
    'DATABASE_URL': 'sqlite:///./db.sqlite3',
}

def app_secret_key():
    return get_env('APP_SECRET_KEY') or get_env('DJANGO_SECRET_KEY')
```

- [ ] **Step 2: Session + CSRF 工具**

Create `app/middleware/session_csrf.py`:

```python
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
```

- [ ] **Step 3: chat router**

Create `app/routers/chat.py`:

```python
import asyncio

from fastapi import APIRouter, Request, Form, HTTPException
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
```

- [ ] **Step 4: 更新 chat.html 为 Jinja2**

Replace `templates/chat.html` 核心表单部分：

```html
{% extends 'base.html' %}

{% block content %}
    <h1>开始会话</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">
        <p>
            <label>sessionId:</label>
            <input type="text" name="sessionId" value="{{ session_id }}">
        </p>
        <p>
            <label>chat:</label>
            <input type="text" name="chat" value="{{ chat }}">
        </p>
        <button type="submit">发送</button>
    </form>
    {% if data %}
        <h3>{{ message }}</h3>
        <div class="chat-results" id="chat-results">
            <ul>
                {% for result in data %}
                    <li style="color: {% if result.type == 'human' %}orange{% else %}slategrey{% endif %}">
                        {% if result.type == 'human' %}客户: {% endif %}
                        {% if result.type == 'ai' %}AI机器人: {% endif %}
                        {{ result.content }}
                    </li>
                {% else %}
                    <li>没有找到搜索结果。</li>
                {% endfor %}
            </ul>
        </div>
    {% endif %}
{% endblock %}
```

- [ ] **Step 5: main.py 注册 Session + chat router**

```python
import os
from starlette.middleware.sessions import SessionMiddleware

from app.routers import chat
from config import app_secret_key

app.add_middleware(SessionMiddleware, secret_key=app_secret_key())
app.include_router(chat.router)
```

- [ ] **Step 6: 重写 test_chat_csrf.py**

```python
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_chat_post_without_csrf_returns_403():
    client = TestClient(app)
    response = client.post("/api/chat", data={"chat": "hello", "sessionId": "abc"})
    assert response.status_code == 403


def test_chat_post_with_csrf_returns_200():
    client = TestClient(app)
    client.get("/api/chat")
    csrf = client.cookies.get("session", "")
    # 从 session 取 token：先 GET 页面解析 hidden input
    get_resp = client.get("/api/chat")
    import re

    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_resp.text)
    assert match, "csrf token not in form"
    token = match.group(1)

    with patch("app.routers.chat.flow_control", return_value=[]):
        response = client.post(
            "/api/chat",
            data={"chat": "hello", "sessionId": "abc", "csrfmiddlewaretoken": token},
        )
    assert response.status_code == 200
```

- [ ] **Step 7: 删除 tests/test_urls.py；运行测试**

```bash
pytest tests/test_chat_csrf.py tests/test_app_health.py -v
```

- [ ] **Step 8: Commit**

```bash
git add app/ templates/chat.html config.py tests/test_chat_csrf.py
git rm tests/test_urls.py
git commit -m "feat: migrate chat endpoint to FastAPI with session CSRF"
```

---

## Task 6 (L4b): KB 与文件预览路由

**Files:**
- Create: `app/routers/kb.py`
- Create: `app/routers/files.py`
- Modify: `app/main.py`
- Modify: `config.py`（`MEDIA_ROOT`、`KB_FILE_ROOT`、`IMAGE_DIR`）
- Create: `tests/test_kb_routes_smoke.py`

**Interfaces:**
- Produces: 与 `fly_base/urls.py` 路径一致的 KB/file 端点

- [ ] **Step 1: config.py 路径常量**

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS.update({
    'MEDIA_ROOT': str(BASE_DIR / 'storage'),
    'KB_FILE_ROOT': str(BASE_DIR / 'storage' / 'kb_file'),
    'IMAGE_DIR': str(BASE_DIR / 'storage' / 'image_file'),
})

def media_root():
    return get_env('MEDIA_ROOT')

def kb_file_root():
    return get_env('KB_FILE_ROOT')

def image_dir():
    return get_env('IMAGE_DIR')
```

- [ ] **Step 2: files router**

Create `app/routers/files.py`:

```python
import mimetypes
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from config import image_dir
from sale_app.config.log import Logger

logger = Logger("fly_base")
router = APIRouter()


@router.get("/file/image-preview/{file_name}")
async def image_preview(file_name: str):
    image_file_path = os.path.join(image_dir(), file_name)
    if not os.path.exists(image_file_path):
        logger.info(f"Image file not found: {image_file_path}")
        raise HTTPException(status_code=404, detail="Image not found")
    mime_type, _ = mimetypes.guess_type(image_file_path)
    with open(image_file_path, "rb") as image_file:
        return Response(content=image_file.read(), media_type=mime_type or "application/octet-stream")
```

- [ ] **Step 3: kb router（从 kb_api.py 移植逻辑）**

Create `app/routers/kb.py`，实现：

- `GET/POST /kb/upload_file` → 渲染 `upload_document.html` / 保存文件 + `KBService.parse` 或 `xlsx_qa_upload`
- `GET/POST /kb/search` → `recall_test.html` + 三种 search
- `GET/POST /kb/create_collection`
- `POST /kb/upload_and_read_excel`
- `POST /kb/text_insert_milvus`

文件保存示例：

```python
import os
import shutil
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from app.templates_env import templates
from config import kb_file_root
from sale_app.core.kb.kb_sevice import KBService

router = APIRouter()


def _save_upload(upload: UploadFile) -> str:
    os.makedirs(kb_file_root(), exist_ok=True)
    dest = os.path.join(kb_file_root(), upload.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return dest
```

Jinja2 模板中若有 `{% csrf_token %}` / `{{ form.as_p }}`，改为显式字段（与 Django form 字段名一致：`collection_name`、`query`、`file_name`、`query_type`、`upload_type` 等）。

- [ ] **Step 4: 注册 routers**

```python
from app.routers import chat, kb, files

app.include_router(kb.router)
app.include_router(files.router)
```

- [ ] **Step 5: 烟测 GET 页面**

Create `tests/test_kb_routes_smoke.py`:

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_page_get():
    assert client.get("/kb/upload_file").status_code == 200


def test_search_page_get():
    assert client.get("/kb/search").status_code == 200


def test_create_collection_get():
    assert client.get("/kb/create_collection").status_code == 200
```

- [ ] **Step 6: Commit**

```bash
pytest tests/test_kb_routes_smoke.py -v
git add app/routers/kb.py app/routers/files.py config.py tests/test_kb_routes_smoke.py app/main.py
git commit -m "feat: migrate KB and file preview routes to FastAPI"
```

---

## Task 7 (L5): SQLAlchemy ORM 替换 Django

**Files:**
- Create: `sale_app/database/sqlalchemy_models.py`
- Create: `sale_app/database/session.py`
- Modify: `sale_app/database/product.py`
- Modify: `import_data_to_sqlite.py`
- Create: `tests/test_product_repository.py`

**Interfaces:**
- Produces: `get_db_session()` context manager；`Product` ORM 映射表 `sale_app_product`

- [ ] **Step 1: SQLAlchemy 模型（对齐 Django 表名）**

Create `sale_app/database/sqlalchemy_models.py`:

```python
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "sale_app_product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(16))
    product_priority: Mapped[int] = mapped_column(Integer, default=1)
    product_type: Mapped[int] = mapped_column(Integer, default=1)
    product_info: Mapped[str] = mapped_column(String(256))


class Dataset(Base):
    __tablename__ = "sale_app_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, default=1)
    dataset_name: Mapped[str] = mapped_column(String(16))
    dataset_type: Mapped[int] = mapped_column(Integer, default=1)
    dataset_info: Mapped[str] = mapped_column(String(256))
    dataset_status: Mapped[int] = mapped_column(Integer, default=1)
    embedding_model: Mapped[str] = mapped_column(String(16))
    embedding_model_provider: Mapped[str] = mapped_column(String(16))
    dataset_create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dataset_update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: session.py**

Create `sale_app/database/session.py`:

```python
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import get_env

engine = create_engine(
    get_env("DATABASE_URL"),
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_db_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

- [ ] **Step 3: 改写 product.py**

```python
from config import recommend_collection_name
from sale_app.config.log import Logger
from sale_app.core.kb.kb_sevice import KBService
from sale_app.database.session import get_db_session
from sale_app.database.sqlalchemy_models import Product

logger = Logger("fly_base")


def get_product_info(user_info: str):
    product_str = ""
    logger.info(f"提取用户信息:{user_info}")
    if user_info in "暂无用户信息":
        with get_db_session() as session:
            products = session.query(Product).all()
            for p in products:
                product_str += f"产品名称：{p.product_name}\n产品信息：{p.product_info}\n"
    else:
        product_str = KBService.hybrid_search(user_info, recommend_collection_name())
    return product_str
```

- [ ] **Step 4: import_data_to_sqlite.py 去 Django**

```python
import json
import os

import dotenv

dotenv.load_dotenv()

from sale_app.database.session import get_db_session, engine
from sale_app.database.sqlalchemy_models import Base, Product


def load_data(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def import_data(data):
    with get_db_session() as session:
        for item in data:
            session.add(Product(**item))
        session.commit()


def main():
    Base.metadata.create_all(bind=engine)
    data = load_data("sale_app/migrations/init_sqllite.json")
    import_data(data)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 单测**

Create `tests/test_product_repository.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sale_app.database.sqlalchemy_models import Base, Product


def test_product_model_roundtrip():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        session.add(
            Product(
                product_name="测试贷",
                product_priority=1,
                product_type=1,
                product_info="info",
            )
        )
        session.commit()
        row = session.query(Product).one()
        assert row.product_name == "测试贷"
```

- [ ] **Step 6: Commit**

```bash
pytest tests/test_product_repository.py -v
git add sale_app/database/ import_data_to_sqlite.py tests/test_product_repository.py
git commit -m "refactor: replace Django ORM with SQLAlchemy for Product access"
```

---

## Task 8 (L6): 移除 Django + 测试/README 收尾

**Files:**
- Delete: `manage.py`, `fly_base/`, `sale_app/chat_api/api.py`, `sale_app/chat_api/kb_api.py`, `sale_app/chat_api/file.py`
- Delete: `sale_app/chat_api/forms/`（若路由已不依赖）
- Delete: `sale_app/models.py`（逻辑已迁至 sqlalchemy_models）
- Modify: `tests/test_settings_env.py`（去掉 django.setup）
- Modify: `README.md`
- Modify: `requirements.txt`（确认无 Django）

**Interfaces:**
- Produces: 启动命令仅 `uvicorn app.main:app`；`rg "from django" sale_app app` 无运行时 import

- [ ] **Step 1: 确认无 django import**

```bash
rg "from django|import django" sale_app/ app/ import_data_to_sqlite.py
```

若有残留，逐一移除或替换。

- [ ] **Step 2: 删除 Django 入口文件**

```bash
git rm manage.py
git rm -r fly_base/
git rm sale_app/chat_api/api.py sale_app/chat_api/kb_api.py sale_app/chat_api/file.py
git rm sale_app/models.py
git rm -r sale_app/chat_api/forms/
```

- [ ] **Step 3: 更新 test_settings_env.py**

```python
from config import get_env


def test_service_api_url_has_no_leading_equals():
    url = get_env("SERVICE_API_URL")
    assert url.startswith("http")
    assert not url.startswith("=")
```

- [ ] **Step 4: 更新 README.md 启动段**

```markdown
## 启动项目

1. Python 3.10 或 3.11 推荐
2. pip install -r requirements.txt
3. 复制 `.env.example` 为 `.env` 并填写密钥
4. 首次升级 LangGraph 1.x 后，删除旧会话库：
   `del storage\\memory_file\\chat_history.db`（Windows）或 `rm storage/memory_file/chat_history.db`
5. python import_data_to_sqlite.py  # 新环境
6. 启动 Milvus（docker 目录下 compose）
7. uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
8. 访问 http://127.0.0.1:8000/api/chat 与 http://127.0.0.1:8000/kb/upload_file
```

- [ ] **Step 5: 全量测试**

```bash
pytest tests/ -v
```

Expected: 全部 PASS

- [ ] **Step 6: 手动烟测**

```bash
uvicorn app.main:app --port 8000
```

- [ ] **Step 7: Commit**

```bash
git add README.md tests/test_settings_env.py requirements.txt
git commit -m "chore: remove Django runtime and document FastAPI startup"
```

---

## 验收清单（全部 Task 完成后）

```bash
# 1) 依赖与版本
python -c "import langgraph; assert langgraph.__version__.startswith('1.')"
rg "pydantic_v1|from django" sale_app/ app/  # 无匹配

# 2) 测试
pytest tests/ -v

# 3) 启动
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 4) 页面
# GET /api/chat, /kb/upload_file, /kb/search — 200
# POST /api/chat 无 CSRF — 403
```

---

## 执行顺序与并行

| 顺序 | Task | 依赖 |
|------|------|------|
| 1 | Task 1 L1 依赖 | 无 |
| 2 | Task 2 L2a Pydantic | Task 1 |
| 3 | Task 3 L2b Checkpoint | Task 1–2 |
| 4 | Task 4 L3 FastAPI 骨架 | Task 3 |
| 5 | Task 5 L4a Chat | Task 4 |
| 6 | Task 6 L4b KB/Files | Task 4 |
| 7 | Task 7 L5 SQLAlchemy | Task 1（可与 5–6 并行，但 L6 前必须完成） |
| 8 | Task 8 L6 清理 | Task 5–7 |

**推荐：** Subagent-Driven，每 Task 一个 implementer + reviewer。

---

## Spec 覆盖自检

| Spec 章节 | Task |
|-----------|------|
| L1 依赖 1.x | Task 1 |
| Pydantic v2 | Task 2 |
| SqliteSaver context + lifespan | Task 3, 4 |
| FastAPI 路由对照 | Task 5, 6 |
| SQLAlchemy ORM | Task 7 |
| 删除 Django、README | Task 8 |
| Postgres/SSE/鉴权重命名 | 不在本计划 |
