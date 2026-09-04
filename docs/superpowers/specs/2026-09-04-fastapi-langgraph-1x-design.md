# FastAPI + LangGraph 1.x 升级设计规格

> 日期：2026-09-04  
> 状态：已评审（用户确认 OK）  
> 前置：Phase A–C 已完成（`feat/project-optimization` 分支）

## 1. 背景与目标

### 1.1 背景

当前项目以 **Django 5** 提供 Web 层，**LangGraph 0.0.55** + **LangChain 0.2.x** 驱动多智能体工作流，SQLite 持久化 checkpoint 与业务数据。Phase A–C 已修复安全、图路由、依赖钉版本、懒加载等问题，但 Web 层同步阻塞、依赖栈已严重落后官方 1.x 生态。

### 1.2 目标

**同一交付周期内完成：**

1. **Web 框架迁移**：Django → **FastAPI**（uvicorn 启动）
2. **AI 栈升级**：**LangGraph 1.2.x** + **LangChain Core 1.x** 全栈对齐
3. **Checkpoint**：继续使用 **SQLite**，采用 `langgraph-checkpoint-sqlite` 新 API
4. **成功标准（严格 1.x）**：依赖、结构化输出、RAG/KB、智谱/Milvus 适配到可安装、可测试、可跑通主链路；**不保留**旧 checkpoint 格式（`chat_history.db` 可删除重建）

### 1.3 非目标（本规格不实施）

| 项 | 说明 |
|----|------|
| PostgresSaver | 属 Phase B，另开计划 |
| SSE / 流式聊天 | 属 Phase C |
| 目录重命名 secrity/moudel/mutil | 另开 PR |
| KB 全量鉴权 + 去掉全部 csrf_exempt | 属 Phase E；本阶段 KB 可暂保留无 CSRF（内网/API Key 占位） |
| 前置安全规则引擎 / 异步队列 | 产品策略，后续 |

---

## 2. 方案选择

### 2.1 已确认决策

| 决策点 | 选择 |
|--------|------|
| LangGraph 目标版本 | **1.x**（实施时钉 `langgraph==1.2.x` 最新可解析版） |
| Checkpoint | **SQLite** + `langgraph-checkpoint-sqlite` |
| 旧 chat_history.db | **丢弃重建**（README 说明） |
| 成功标准 | **全栈严格 1.x**（非最小 shim） |
| Web 框架 | **FastAPI**，与 LangGraph 升级 **同一期** |
| 实施策略 | **方案 B：分层升级**（非一次大爆炸、非兼容垫片） |

### 2.2 分层顺序（L1–L6）

```
L1 依赖窗 → L2 LangGraph/checkpoint/Pydantic → L3 FastAPI 骨架
         → L4 路由迁移 → L5 SQLAlchemy ORM → L6 清理 Django
```

每层独立可验证、可回滚（git revert 单 commit 或单层）。

---

## 3. 目标架构

### 3.1 运行时拓扑

```text
uvicorn app.main:app --host 0.0.0.0 --port 8000

app/main.py
  ├─ StaticFiles /static
  ├─ Jinja2Templates templates/
  ├─ TraceIdMiddleware（自 sale_app.util.traceid_ware 迁移/适配）
  ├─ app/routers/chat.py      GET/POST /api/chat
  ├─ app/routers/kb.py          /kb/*
  └─ app/routers/files.py       /file/image-preview/{fileName}

业务层（保留 sale_app/ 包，去 Django 依赖）：
  handle_core.flow_control
    → pre_handle (secrity)
    → run_flow → get_chain()
         → build_flow_graph(llm)
         → compile(checkpointer=SqliteSaver 1.x)
         → invoke
```

### 3.2 新增目录结构

```text
app/
  __init__.py
  main.py                 # FastAPI 工厂、lifespan、静态/模板
  dependencies.py         # 可选：DB session、配置
  middleware/
    trace_id.py           # 从 Django TraceIdMiddleware 移植
  routers/
    chat.py
    kb.py
    files.py
  schemas/                # Pydantic v2 请求/响应（替代 Django Forms 部分）
    chat.py
    kb.py
sale_app/                 # 业务逻辑保留，逐步去掉 django.* import
  database/
    sqlalchemy_models.py  # Product, Datasets
    session.py            # engine + SessionLocal
  core/                   # 不变更职责，仅适配 1.x API
config.py                 # 继续 .env + DEFAULTS
```

### 3.3 路由对照表

| Django (fly_base/urls.py) | FastAPI | 方法 |
|---------------------------|---------|------|
| `api/chat` | `/api/chat` | GET 页面 / POST 提交 |
| `kb/upload_file` | `/kb/upload_file` | GET/POST |
| `kb/search` | `/kb/search` | GET/POST |
| `kb/create_collection` | `/kb/create_collection` | POST |
| `kb/upload_and_read_excel` | `/kb/upload_and_read_excel` | POST |
| `kb/text_insert_milvus` | `/kb/text_insert_milvus` | POST |
| `file/image-preview/<fileName>` | `/file/image-preview/{file_name}` | GET |

路径与 query/body 字段名 **保持与现有模板/前端一致**，减少模板改动。

---

## 4. LangGraph 1.x 升级要点

### 4.1 依赖（目标示意，实施时以 pip 解析为准）

```text
langgraph==1.2.x
langgraph-checkpoint>=4.1.0,<5
langgraph-checkpoint-sqlite>=2.x
langchain-core>=1.4.7,<2
langchain>=1.3.x,<2
langchain-openai>=0.3.x  # 与 core 1.x 兼容版本
langchain-community>=0.3.x  # 按 Milvus/文档 loader 需要
langchain-milvus / pymilvus  # 升到与 core 1.x 兼容集
langchain-zhipu  # 验证与 core 1.x + httpx 兼容
pydantic>=2.7.4,<3
```

移除或替换：`pytest-django` → `httpx`（TestClient）、`pytest-asyncio`（若测 async 路由）。

### 4.2 Checkpoint 生命周期

**现状（0.0.55）：**

```python
from langgraph.checkpoint.sqlite import SqliteSaver
memory = SqliteSaver.from_conn_string(db_path)
_chain = graph.compile(checkpointer=memory)
```

**目标（1.x + checkpoint-sqlite）：**

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# from_conn_string 为 context manager；进程内单例需明确 enter/exit 或 lifespan 管理
with SqliteSaver.from_conn_string(db_path) as checkpointer:
    _chain = graph.compile(checkpointer=checkpointer)
```

**要求：**

- 在 FastAPI `lifespan` 中创建/关闭 checkpointer，或模块级单例 + `atexit`/lifespan shutdown
- 旧 `storage/memory_file/chat_history.db` 不兼容时：日志提示删除文件后重启
- 测试使用 `MemorySaver` 或临时 SQLite 文件，避免污染开发库

### 4.3 Pydantic / 结构化输出

全项目移除 `langchain_core.pydantic_v1`，改为 **Pydantic v2**：

```python
# 前
from langchain_core.pydantic_v1 import BaseModel, Field

# 后
from pydantic import BaseModel, Field
```

涉及文件（非穷举）：`information_gathering.py`、`intention_confirm.py`、`qa_handle.py`、`fix_question.py`、`pre_safety.py`。

`llm.with_structured_output(Model)` 行为以 core 1.x 文档为准；单测 mock LLM 验证 invoke 不崩溃。

### 4.4 图 API

保留现有节点名、`NextNode` 常量、`build_flow_graph` / `get_chain` / `run_flow` 对外签名。

需验证在 1.x 下仍有效的 API：

- `StateGraph`, `END`, `add_node`, `add_conditional_edges`, `set_entry_point`, `compile`
- 子图 `build_recommend_graph(llm).compile()` 作为节点

若 1.x 对 `TypedDict` state 或 `Annotated[..., operator.add]` 有变更，按官方迁移指南调整。

---

## 5. FastAPI Web 层设计

### 5.1 应用入口

```python
# app/main.py（示意）
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.middleware.trace_id import TraceIdMiddleware
from app.routers import chat, kb, files
from sale_app.core.mutil.flow_graph import shutdown_chain, startup_chain


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_chain()  # 可选：预热；或保持懒加载
    yield
    shutdown_chain()  # 关闭 SqliteSaver context


app = FastAPI(lifespan=lifespan)
app.add_middleware(TraceIdMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(chat.router)
app.include_router(kb.router)
app.include_router(files.router)
```

### 5.2 聊天路由

- **GET** `/api/chat`：渲染 `chat.html`，表单含 `sessionId`、`chat`
- **POST** `/api/chat`：`application/x-www-form-urlencoded` 或 `multipart/form-data`（与现模板一致）
- 调用 `flow_control(chat, session_id)` 使用 `asyncio.to_thread` 避免阻塞事件循环
- **CSRF**：使用 `starlette.middleware.sessions.SessionMiddleware` + 表单 hidden token，或 FastAPI 依赖校验 Referer/Origin（开发环境可配置 `DEBUG` 放宽）；需有 TestClient 测试 403/200

### 5.3 KB / 文件路由

- 从 `sale_app/chat_api/kb_api.py`、`file.py` 提取逻辑到 `app/routers/kb.py`、`files.py`
- 文件上传：`UploadFile` + 写入 `settings.MEDIA_ROOT` 等价路径（`config.py` / 常量 `KB_FILE_ROOT`）
- 本阶段 **不要求** KB 端点 CSRF；文档标注「生产需鉴权」

### 5.4 配置迁移

| Django settings | FastAPI / config.py |
|-----------------|---------------------|
| `SECRET_KEY` | `DJANGO_SECRET_KEY` → 重命名为 `APP_SECRET_KEY` 或复用 env 名并文档说明 |
| `MEDIA_ROOT` / `KB_FILE_ROOT` | `config.py` 或 `app/config.py` 常量 |
| `STATICFILES_DIRS` | FastAPI `StaticFiles` |
| `DATABASES sqlite` | SQLAlchemy `DATABASE_URL=sqlite:///./db.sqlite3` |

`.env.example` 补充：`DATABASE_URL`、`APP_SECRET_KEY`（session 用）。

---

## 6. 数据层：Django ORM → SQLAlchemy

### 6.1 模型

迁移 `sale_app/models.py` 中：

- `Product`（product_name, product_priority, product_type, product_info）
- `Datasets`（现有字段保持列名一致）

使用 SQLAlchemy 2.0 style `DeclarativeBase`，表名与 Django 默认一致（`sale_app_product` 等），避免动 `db.sqlite3` 结构。

### 6.2 访问层

- `sale_app/database/product.py` 改为 SQLAlchemy 查询或保留函数签名、内部换实现
- `import_data_to_sqlite.py` 改为 SQLAlchemy bulk insert 或保留 JSON 导入逻辑

### 6.3 迁移策略

- **不运行 Django migrations** 作为运行时依赖
- 已有 `db.sqlite3` 直接只读/读写；新环境执行 `import_data_to_sqlite.py` + migrate 文档说明

---

## 7. 错误处理与可观测性

| 场景 | 行为 |
|------|------|
| checkpoint DB 版本不兼容 | 记录 error，提示删除 `chat_history.db`，返回 503 或友好 HTML 错误页 |
| `pre_handle` LLM 失败 | 保持 Phase A–C 行为：返回 `None` 放行主流程 |
| Milvus 不可达 | KB/QA 路由返回明确错误 JSON/HTML，不 500 裸栈 |
| TraceId | 每个请求生成/传递 `X-Trace-Id`，日志 handler 继续关联 |

LangSmith：保留 `LANGCHAIN_API_KEY` 环境变量支持（若现有代码使用）。

---

## 8. 测试策略

### 8.1 框架

- `pytest` + `httpx.AsyncClient` / `starlette.testclient.TestClient`
- 移除 `pytest-django` 依赖
- 图/LLM 测试继续 mock，不依赖真实 API Key

### 8.2 必测项

| 类别 | 内容 |
|------|------|
| 依赖 | `test_imports_smoke.py`：django 不可 import 为运行时依赖；langgraph 1.x、core 1.x |
| 图 | 现有 `test_decide_router.py`、`test_flow_lazy_init.py` 通过 |
| Checkpoint | compile 烟测（MemorySaver 或 temp sqlite） |
| FastAPI | `/api/chat` GET 200；POST 无 CSRF 403、有 token 200 |
| KB | `test_kb_service_parse_dispatch.py` 及默认 collection 测试 |
| ORM | Product 查询单测（内存 sqlite 或 fixture db） |

### 8.3 验收命令

```bash
pip install -r requirements.txt
pytest tests/ -v
uvicorn app.main:app --port 8000
# 手动：/api/chat、/kb/upload_file
```

---

## 9. 清理与文档

### 9.1 删除或归档（L6）

- 停止维护：`manage.py`、`fly_base/`（settings/urls/wsgi/asgi）
- `sale_app/chat_api/api.py`、`kb_api.py` 逻辑迁至 `app/routers/` 后可删或留 thin re-export（推荐删除避免双入口）
- `requirements.txt` 移除 `Django`、`pytest-django`

### 9.2 README 更新

- 启动命令改为 uvicorn
- Python **3.10+**（推荐 3.10 / 3.11；3.13 可能因 numpy/依赖无解）
- 升级后 **删除** `storage/memory_file/chat_history.db` 说明
- Milvus docker 步骤保留

---

## 10. 风险与缓解

| 风险 | 缓解 |
|------|------|
| langchain-zhipu 与 core 1.x 不兼容 | 提前在干净 venv 试装；必要时 fork 版本或改用 OpenAI 兼容 base_url 仅 ChatOpenAI |
| langchain-milvus 与 1.x 断裂 | 锁定兼容版本；最坏情况暂时直连 pymilvus 封装 |
| SqliteSaver context 生命周期 | FastAPI lifespan 统一管理；单测 fixture 显式 close |
| 大范围依赖冲突 | 分层 L1 单独 PR/commit，每层 green 再继续 |
| 模板 CSRF 与 Session | 先实现最小 SessionMiddleware + csrf_token 与 Django 行为对齐 |

---

## 11. 回滚策略

- 每层独立 commit；回滚 `git revert` 该层 commit
- 保留 `feat/project-optimization` 分支；未合并前 main 仍 Django
- 依赖回滚：恢复 Phase A–C 的 `requirements.txt` pin

---

## 12. 批准记录

| 项 | 确认 |
|----|------|
| LangGraph 1.x + 全栈 1.x | ✅ |
| SQLite checkpoint 新 API | ✅ |
| 旧 chat_history 可丢弃 | ✅ |
| FastAPI 同批迁移 | ✅ |
| 分层方案 B（L1–L6） | ✅ |
| 用户确认日期 | 2026-09-04 |

---

## 13. 下一步

1. 用户审阅本 spec（本文档）
2. 编写实施计划：`docs/superpowers/plans/2026-09-04-fastapi-langgraph-1x.md`
3. Subagent-Driven 或 Inline 执行 L1–L6
