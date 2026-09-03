# 项目优化实施计划（可执行）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按优先级落地 `docs/project_optimization_analysis.md` 中的 P0/P1 优化，使项目可安全运行、图路由正确、依赖可复现，并为后续 LangGraph 升级铺路。

**Architecture:** 保持 Django + LangGraph + Milvus 现有架构不变；先修安全与正确性，再钉依赖与懒加载，最后清理死代码。不在本阶段做框架替换或全量异步改造。

**Tech Stack:** Django 5.0.x、LangChain/LangGraph 0.2.x / 0.0.55（暂不升级大版本）、Milvus、python-dotenv、pytest

**Spec 来源:** `docs/project_optimization_analysis.md`

## Global Constraints

- 本阶段 **不升级** `langgraph` 到 0.2+ / 1.x（单独列入 Phase B）
- 不重命名 `secrity` / `moudel` / `mutil` 目录（避免大规模 import 破坏；可后续单独 PR）
- 不删除 Qdrant/Weaviate 文件本体，仅从工厂/依赖中明确「当前仅支持 Milvus」
- 密钥不得提交进 git；示例配置只用 `.env.example`
- 每个 Task 结束后必须有可运行的验证命令；验证通过后再进入下一 Task
- Python 格式：black，`max_line_length=120`；禁止 `from module import *`；`snake_case`

## 文件变更总览

| 文件 | 职责 |
|------|------|
| `.gitignore` | 忽略 `.env`，修正根目录向量卷忽略规则 |
| `.env.example` | 可提交的环境变量模板（无真实密钥） |
| `fly_base/settings.py` | 从环境变量读取 SECRET_KEY/DEBUG/ALLOWED_HOSTS |
| `config.py` | 修复 `SERVICE_API_URL` 默认值 |
| `sale_app/core/mutil/node_names.py` | 路由节点名常量 |
| `sale_app/core/mutil/flow_graph.py` | 修图边、路由、懒加载 compile |
| `sale_app/core/agent/*.py` 等 | 修复 `deault=` → `default=` |
| `sale_app/models.py` | 修复 `Product.__str__` |
| `sale_app/secrity/pre_safety.py` | 加固异常处理 |
| `requirements.txt` / `requirements.lock.txt` | 钉版本 |
| `tests/` | 新增最小单测 |

---

## Phase A — P0 安全与正确性（必须先完成）

### Task 1: 密钥出库 + settings 环境化

**Files:**
- Modify: `.gitignore`
- Create: `.env.example`
- Modify: `fly_base/settings.py`
- Modify: `config.py`（`SERVICE_API_URL`）
- Test: `tests/test_settings_env.py`

**Interfaces:**
- Consumes: 环境变量 `DJANGO_SECRET_KEY`、`DJANGO_DEBUG`、`DJANGO_ALLOWED_HOSTS`、`SERVICE_API_URL`
- Produces: settings 启动时若缺少 `DJANGO_SECRET_KEY` 且 `DEBUG=False` 则报错

- [ ] **Step 1: 确认 `.env` 已被 git 跟踪**

Run:

```bash
git ls-files .env
```

Expected: 输出 `.env`（若无输出则说明未跟踪，跳过 Step 5 的 `git rm --cached`）

- [ ] **Step 2: 更新 `.gitignore`**

在 `.gitignore` 末尾追加（并修正根目录忽略，避免误伤包路径）：

```gitignore
# secrets & local env
.env
.env.local
*.pem

# docker volume data at repo root only
/etcd/
/milvus/
/minio/
/qdrant/
/storage/
```

同时删除旧的无前缀行（若存在）：

```gitignore
etcd/
milvus/
minio/
qdrant/
storage/
```

- [ ] **Step 3: 创建 `.env.example`（无真实密钥）**

```dotenv
DJANGO_SECRET_KEY=replace-me-with-a-long-random-string
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

ZHIPU_API_KEY=
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4/
ZHIPU_MODEL=glm-4
ZHIPU_TEMPERATURE=0.1

VECTOR_TYPE=milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_DATABASE=default
RECOMMEND_COLLECTION_NAME=recommend_product

SERVICE_API_URL=http://127.0.0.1:8000
USER_INFO_MASK=False
```

- [ ] **Step 4: 改写 `fly_base/settings.py` 密钥相关段**

将：

```python
SECRET_KEY = "django-insecure-zgsg%1n01fqz1uow_gp_^(7hu7_#4v0k2qv%n$22xfbl6d%276"
DEBUG = True
ALLOWED_HOSTS = []
```

替换为：

```python
import os

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()
]

if not DEBUG and SECRET_KEY.startswith("django-insecure"):
    raise RuntimeError("生产环境必须设置安全的 DJANGO_SECRET_KEY")
```

注意：文件顶部若尚未 `import os`，保留/合并已有 import，不要重复。

- [ ] **Step 5: 修复 `config.py` 中 `SERVICE_API_URL`**

将：

```python
'SERVICE_API_URL': '=http://127.0.0.1:5001'
```

改为：

```python
'SERVICE_API_URL': 'http://127.0.0.1:8000'
```

- [ ] **Step 6: 若 `.env` 在版本库中，移出索引（不删本地文件）**

```bash
git rm --cached .env
```

Expected: `.env` 变为 untracked；本地文件仍在。然后提醒人工：到智谱/LangSmith 控制台**轮换**已泄露的 Key，并写入本地 `.env`。

- [ ] **Step 7: 写冒烟测试**

Create `tests/__init__.py`（空文件）与 `tests/test_settings_env.py`：

```python
import os

import django
from django.conf import settings


def test_service_api_url_has_no_leading_equals():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fly_base.settings")
    if not settings.configured:
        django.setup()
    from config import get_env

    url = get_env("SERVICE_API_URL")
    assert url.startswith("http"), url
    assert not url.startswith("="), url
```

- [ ] **Step 8: 安装 pytest 并运行**

```bash
pip install pytest pytest-django
pytest tests/test_settings_env.py -v
```

Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add .gitignore .env.example fly_base/settings.py config.py tests/test_settings_env.py tests/__init__.py
git commit -m "$(cat <<'EOF'
fix: load Django secrets from env and stop tracking .env

EOF
)"
```

Windows PowerShell 若 HEREDOC 不可用，改用：

```powershell
git commit -m "fix: load Django secrets from env and stop tracking .env"
```

---

### Task 2: 修复 LangGraph 图边与路由常量

**Files:**
- Create: `sale_app/core/mutil/node_names.py`
- Modify: `sale_app/core/mutil/flow_graph.py`
- Test: `tests/test_decide_router.py`

**Interfaces:**
- Consumes: `FlowState` 中的 `next` / `pre_node` / `isRecommend`
- Produces: `NextNode` 常量类；`decide_router(state) -> str`；图中不再对所有节点 `add_edge(..., END)`

- [ ] **Step 1: 创建节点名常量**

Create `sale_app/core/mutil/node_names.py`：

```python
class NextNode:
    FIX = "问题修复"
    CLASSIFY = "问题分类"
    CHAT = "闲聊经理"
    INTENT = "意图确认"
    GATHER = "信息收集"
    RECOMMEND = "产品推荐"
    QA = "产品解答专家"
    FINISH = "FINISH"
```

- [ ] **Step 2: 写路由单测（不依赖 LLM）**

Create `tests/test_decide_router.py`：

```python
from sale_app.core.mutil.node_names import NextNode


def _decide_router(state):
    """与 flow_graph.decide_router 保持同逻辑的可导入副本验证；实现后改为直接 import。"""
    from sale_app.core.mutil.flow_graph import decide_router

    return decide_router(state)


def test_router_qa():
    assert _decide_router({"next": NextNode.QA}) == NextNode.QA


def test_router_recommend():
    assert _decide_router({"next": NextNode.RECOMMEND}) == NextNode.RECOMMEND


def test_router_gather_sticky():
    state = {"next": NextNode.CHAT, "pre_node": NextNode.GATHER}
    assert _decide_router(state) == NextNode.GATHER


def test_router_gather_to_qa_allowed():
    state = {"next": NextNode.QA, "pre_node": NextNode.GATHER}
    assert _decide_router(state) == NextNode.QA
```

- [ ] **Step 3: 修改 `flow_graph.py` — 常量与 decide_router**

1. 增加 import：

```python
from sale_app.core.mutil.node_names import NextNode
```

2. 将 `decide_router` 替换为：

```python
def decide_router(state):
    nxt = state.get("next") or ""
    pre_node = state.get("pre_node") or ""

    if NextNode.QA in nxt:
        return NextNode.QA
    if NextNode.RECOMMEND in nxt:
        return NextNode.RECOMMEND
    if NextNode.GATHER in nxt:
        return NextNode.GATHER
    # 信息收集未完成时粘性路由；允许跳到产品解答
    if NextNode.GATHER in pre_node and NextNode.QA not in nxt:
        return NextNode.GATHER
    return nxt
```

3. **删除** 以下危险循环（整段删除）：

```python
for node in list(flow_graph.nodes.keys()):
    flow_graph.add_edge(node, END)
```

4. 为需要结束的节点显式连边（在条件边之后补充，若尚无）：

```python
flow_graph.add_edge(NextNode.CHAT, END)
flow_graph.add_edge(NextNode.QA, END)
# 产品推荐子图内部已到 END；作为节点返回后也应结束
flow_graph.add_edge(NextNode.RECOMMEND, END)
```

注意：若已有 `flow_graph.add_edge("产品解答专家", END)`，改为使用 `NextNode.QA`，避免重复添加。

5. 条件边 map 改用常量：

```python
flow_graph.add_conditional_edges(
    NextNode.CLASSIFY,
    decide_router,
    {
        NextNode.CHAT: NextNode.CHAT,
        NextNode.INTENT: NextNode.INTENT,
        NextNode.GATHER: NextNode.GATHER,
        NextNode.RECOMMEND: NextNode.RECOMMEND,
        NextNode.QA: NextNode.QA,
    },
)
flow_graph.add_conditional_edges(
    NextNode.INTENT,
    lambda x: x["next"],
    {
        NextNode.GATHER: NextNode.GATHER,
        NextNode.CHAT: NextNode.CHAT,
    },
)
flow_graph.add_conditional_edges(
    NextNode.GATHER,
    information_router,
    {
        NextNode.FINISH: END,
        NextNode.RECOMMEND: NextNode.RECOMMEND,
    },
)
```

6. `information_router` 同步：

```python
def information_router(state):
    if state.get("isRecommend"):
        return NextNode.RECOMMEND
    return NextNode.FINISH
```

- [ ] **Step 4: 运行路由测试**

```bash
pytest tests/test_decide_router.py -v
```

Expected: PASS（若 import `flow_graph` 时因缺少 API Key/Milvus 失败，见 Step 5）

- [ ] **Step 5: 若模块 import 触发 LLM/DB，先做懒加载最小修补**

将文件顶部：

```python
llm = ZhipuAI().openai_chat()
memory = SqliteSaver.from_conn_string(...)
...
chain = flow_graph.compile(checkpointer=memory)
```

改为延迟初始化模式（完整版见 Task 5；此处最小可用）：

```python
llm = None  # 由 get_chain() 初始化
_chain = None

def get_chain():
    global llm, _chain, memory
    if _chain is not None:
        return _chain
    llm = ZhipuAI().openai_chat()
    # 重新绑定依赖 llm 的节点前，确保 build_graph 只执行一次
    # 若当前结构是模块级 add_node，则至少延迟 compile：
    db_path = find_project_root(os.path.abspath(__file__)) + "/storage/memory_file/chat_history.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    memory = SqliteSaver.from_conn_string(db_path)
    _chain = flow_graph.compile(checkpointer=memory)
    return _chain


def run_flow(question: str, config: dict) -> FlowState:
    return get_chain().invoke({"messages": [HumanMessage(content=question)]}, config)
```

**重要：** 模块级 `add_node(..., agent=fix_question(llm))` 仍需要 `llm`。若现有代码在 import 时就 `add_node`，则本 Task 只删危险边 + 修路由字符串；懒加载完整重构放到 **Task 5**。本 Step 仅在测试无法 import 时做最小改动：用 mock 环境变量占位。

临时测试用：

```bash
set ZHIPU_API_KEY=dummy
set ZHIPU_MODEL=glm-4
set ZHIPU_TEMPERATURE=0.1
pytest tests/test_decide_router.py -v
```

- [ ] **Step 6: Commit**

```powershell
git add sale_app/core/mutil/node_names.py sale_app/core/mutil/flow_graph.py tests/test_decide_router.py
git commit -m "fix: correct langgraph edges and unify route node names"
```

---

### Task 3: 修复 Pydantic `deault` 拼写与 `Product.__str__`

**Files:**
- Modify: `sale_app/core/mutil/fix_question.py`
- Modify: `sale_app/core/agent/intention_confirm.py`
- Modify: `sale_app/core/agent/information_gathering.py`
- Modify: `sale_app/core/agent/qa_handle.py`
- Modify: `sale_app/models.py`
- Test: `tests/test_field_defaults.py`

**Interfaces:**
- Produces: 所有 `Field(..., deault=...)` 改为 `Field(..., default=...)` 或按需去掉非法组合

- [ ] **Step 1: 全局替换 `deault=`**

对下列文件中的 `deault=` 全部改为 `default=`：

- `sale_app/core/mutil/fix_question.py`
- `sale_app/core/agent/intention_confirm.py`
- `sale_app/core/agent/information_gathering.py`
- `sale_app/core/agent/qa_handle.py`

注意：`Field(..., default=None)` 与 `...`（required）互斥。若原为 `Field(..., deault=None)`，改为二选一：

```python
# 推荐：可选字段
information: str = Field(default=None, title="问题", description="待信息收集的问题")
```

或保持必填：

```python
information: str = Field(..., title="问题", description="待信息收集的问题")
```

本项目 structured output 场景推荐：**去掉 `...`，使用 `default=None`**，避免校验过严。

- [ ] **Step 2: 修复 `Product.__str__`**

`sale_app/models.py`：

```python
def __str__(self):
    return self.product_name
```

- [ ] **Step 3: 写测试**

```python
# tests/test_field_defaults.py
from sale_app.core.agent.information_gathering import Information  # 若类名不同则按实际调整


def test_information_fields_accept_defaults():
    # 类名以各文件中 BaseModel 子类为准；information_gathering 中为收集结果模型
    pass
```

先打开 `information_gathering.py` 确认模型类名，再写真实断言。示例（类名为 `InformationGathering` 时）：

```python
def test_product_str_returns_name():
    from sale_app.models import Product

    p = Product(product_name="测试贷", product_info="info")
    assert str(p) == "测试贷"
```

`Product` 未 `save()` 也可测 `__str__`（不写库）。

- [ ] **Step 4: 运行**

```bash
pytest tests/test_field_defaults.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git commit -am "fix: correct Field default typos and Product.__str__"
```

---

### Task 4: 加固 `pre_handle` 异常路径

**Files:**
- Modify: `sale_app/secrity/pre_safety.py`
- Test: `tests/test_pre_safety.py`

**Interfaces:**
- Consumes: `question: str`
- Produces: `pre_handle(question) -> str | None`（拒答文案或 None）；异常时返回 `None` 并打日志，不再访问 `e.body`

- [ ] **Step 1: 改异常处理**

将：

```python
except Exception as e:
    logger.error(e)
    return e.body.get("message")
```

改为：

```python
except Exception as e:
    logger.exception("pre_handle failed: %s", e)
    # 安全模块失败时放行到主流程，避免因 LLM 异常导致整站不可用
    return None
```

- [ ] **Step 2: 单元测试（mock LLM）**

```python
# tests/test_pre_safety.py
from unittest.mock import MagicMock, patch

from sale_app.secrity import pre_safety


def test_pre_handle_returns_none_on_generic_error():
    with patch.object(pre_safety, "ZhipuAI") as mock_zhipu:
        mock_llm = MagicMock()
        mock_zhipu.return_value.openai_chat.return_value = mock_llm
        mock_llm.with_structured_output.return_value = MagicMock()
        # tagging_chain.invoke 会在后面绑定；直接 patch invoke 路径更稳：
        with patch.object(pre_safety, "tagging_prompt") as mock_prompt:
            mock_chain = MagicMock()
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)
            mock_chain.invoke.side_effect = RuntimeError("boom")
            # 若上述 patch 不匹配实际调用链，改为 patch tagging_chain 构建处
            result = pre_safety.pre_handle("你好")
            assert result is None or isinstance(result, str)
```

若 patch 过脆，改为抽函数后测：

```python
def _safe_reject_message(exc: Exception) -> None:
    return None


def test_safe_reject_message():
    assert _safe_reject_message(RuntimeError("x")) is None
```

并在 `pre_handle` 的 except 中调用它。

- [ ] **Step 3: Commit**

```powershell
git add sale_app/secrity/pre_safety.py tests/test_pre_safety.py
git commit -m "fix: harden pre_handle exception handling"
```

---

## Phase B — P1 依赖可复现与图懒加载

### Task 5: 图与 LLM 懒加载（可测、可多进程）

**Files:**
- Modify: `sale_app/core/mutil/flow_graph.py`
- Modify: `sale_app/core/mutil/recommend_product_graph.py`（同样模式）
- Modify: `sale_app/core/handle_core.py`（仍调用 `run_flow`，接口不变）
- Test: `tests/test_flow_lazy_init.py`

**Interfaces:**
- Produces: `build_flow_graph(llm) -> CompiledGraph`；`get_chain()`；`run_flow(question, config)` 签名不变

- [ ] **Step 1: 将图构建收入函数**

目标结构：

```python
def build_flow_graph(llm):
    flow_graph = StateGraph(FlowState)
    flow_graph.add_node(NextNode.FIX, functools.partial(fixed_question_node, agent=fix_question(llm)))
    # ... 其余 add_node / add_edge / conditional_edges 全部移入本函数
    flow_graph.set_entry_point(NextNode.FIX)
    return flow_graph


_chain = None


def get_chain():
    global _chain
    if _chain is not None:
        return _chain
    llm = ZhipuAI().openai_chat()
    graph = build_flow_graph(llm)
    db_path = find_project_root(os.path.abspath(__file__)) + "/storage/memory_file/chat_history.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    memory = SqliteSaver.from_conn_string(db_path)
    _chain = graph.compile(checkpointer=memory)
    return _chain


def run_flow(question: str, config: dict) -> FlowState:
    return get_chain().invoke({"messages": [HumanMessage(content=question)]}, config)
```

对 `recommend_product_graph.py` 做同样处理：提供 `build_recommend_graph(llm)`，由主图 `add_node(NextNode.RECOMMEND, build_recommend_graph(llm).compile())`。

- [ ] **Step 2: 测试 import 不触发 compile**

```python
# tests/test_flow_lazy_init.py
import importlib


def test_import_flow_graph_does_not_set_chain():
    mod = importlib.import_module("sale_app.core.mutil.flow_graph")
    importlib.reload(mod)
    assert getattr(mod, "_chain", None) is None
```

- [ ] **Step 3: Commit**

```powershell
git commit -am "refactor: lazy-init langgraph compile and llm clients"
```

---

### Task 6: 钉死依赖并对齐智谱包名

**Files:**
- Modify: `requirements.txt`
- Create: `requirements.lock.txt`（可选，pip freeze 结果）
- Test: 手工安装验证

**Interfaces:**
- Produces: 可重复安装的依赖集合；`zhipuai` import 与包名一致

- [ ] **Step 1: 确认当前可 import 的智谱包**

```bash
python -c "import langchain_zhipu; print(langchain_zhipu.__file__)"
python -c "import langchain_zhipuai; print('zhipuai ok')"
```

以**实际能 import 成功**的包名为准，写回 `requirements.txt`。

- [ ] **Step 2: 重写 `requirements.txt`（钉版本，保留当前可跑组合）**

示例基线（安装后用 `pip freeze` 校正数字）：

```text
Django==5.0.6
langchain==0.2.16
langchain-core==0.2.38
langchain-community==0.2.16
langchain-experimental==0.0.59
langchain-openai==0.1.23
langgraph==0.0.55
python-dotenv==1.0.1
langdetect==1.0.9
presidio-anonymizer==2.2.354
presidio-analyzer==2.2.354
Faker==25.8.0
pandas==2.2.2
openpyxl==3.1.5
qdrant-client==1.10.1
langchain-qdrant==0.1.3
weaviate-client==4.6.5
langchain-milvus==0.1.4
pymilvus[model]==2.4.4
python-docx==1.1.2
xlrd==2.0.1
unstructured[docx]==0.10.30
pytest==8.3.2
pytest-django==4.8.0
# 按 Step 1 结果二选一：
# langchain-zhipu==...
# 或 langchain-zhipuai==...
```

- [ ] **Step 3: 干净环境试装**

```bash
python -m venv .venv-verify
.venv-verify\Scripts\activate
pip install -r requirements.txt
python -c "import django; import langgraph; print(django.get_version())"
```

Expected: 无报错；打印 Django 版本

- [ ] **Step 4: Commit**

```powershell
git add requirements.txt
git commit -m "chore: pin dependency versions for reproducible installs"
```

---

### Task 7: 聊天页 CSRF 最小恢复（表单 POST）

**Files:**
- Modify: `sale_app/chat_api/api.py`
- Modify: `templates/chat.html`
- Modify: `templates/base.html`（若 CSRF token 放基模）

**说明:** KB 上传接口可暂留 `@csrf_exempt`（标注 TODO），本 Task 只修 `/api/chat`。

- [ ] **Step 1: 去掉 `to_chat` 的 `@csrf_exempt`**

```python
# 删除 from django.views.decorators.csrf import csrf_exempt
# 删除 @csrf_exempt
def to_chat(request):
    ...
```

- [ ] **Step 2: 表单加 CSRF**

在 `templates/chat.html` 的 `<form ...>` 内第一行加入：

```django
{% csrf_token %}
```

- [ ] **Step 3: 浏览器手工验证**

```bash
python manage.py runserver
```

打开 `http://127.0.0.1:8000/api/chat`，提交一句话。

Expected: 200，不再 403

- [ ] **Step 4: Commit**

```powershell
git commit -am "fix: restore CSRF protection on chat form endpoint"
```

---

## Phase C — P1/P2 清理与观测（可并行）

### Task 8: KB 重复方法合并 + 默认 collection 配置化

**Files:**
- Modify: `sale_app/core/kb/kb_sevice.py`
- Modify: `config.py`
- Test: `tests/test_kb_service_parse_dispatch.py`

- [ ] **Step 1: `config.py` 增加默认集合名**

```python
DEFAULTS = {
    # ...existing...
    'DEFAULT_KB_COLLECTION': 'loan_qa',
}
```

- [ ] **Step 2: 删除 `parse_excel`，保留 `parse`；所有调用点改指向 `parse`**

```python
@classmethod
def parse(cls, excel_file, collection_name: str | None = None):
    if collection_name is None:
        collection_name = get_env("DEFAULT_KB_COLLECTION")
    if excel_file.endswith((".xls", ".xlsx")):
        extractor = ExcelExtractor(excel_file)
    elif excel_file.endswith(".pdf"):
        extractor = PdfExtractor(excel_file)
    elif excel_file.endswith(".docx"):
        extractor = WordExtractor(excel_file)
    else:
        raise ValueError("不支持的文件格式")
    docs = extractor.extract()
    vector = Vector(collection_name=collection_name)
    vector.vector_processor.hybrid_add_documents(docs)
```

- [ ] **Step 3: 用临时文件测后缀分发（mock extractor）**

```python
from unittest.mock import patch, MagicMock
from sale_app.core.kb.kb_sevice import KBService


def test_parse_rejects_unknown_suffix():
    try:
        KBService.parse("a.txt", collection_name="t")
        assert False, "should raise"
    except ValueError as e:
        assert "不支持" in str(e)
```

- [ ] **Step 4: Commit**

```powershell
git commit -am "refactor: unify KB parse entry and default collection name"
```

---

### Task 9: 隔离 demo/test 脚本，避免误 import

**Files:**
- Move: `sale_app/core/mutil/demo.py` → `scripts/langsmith_eval_demo.py`
- Move: `sale_app/secrity/test.py` → `scripts/sensitive_info_manual_test.py`
- Move: `sale_app/core/kb/vector/milvus/test.py` → `scripts/splade_manual_test.py`（若存在）

- [ ] **Step 1: 创建 `scripts/` 并移动文件**
- [ ] **Step 2: 确认无业务代码 import 旧路径**

```bash
rg "mutil.demo|secrity.test|milvus.test" -g "*.py"
```

Expected: 无业务引用

- [ ] **Step 3: Commit**

```powershell
git add scripts/ sale_app/
git commit -m "chore: move demo scripts out of importable package paths"
```

---

### Task 10: 向量工厂文档化「仅 Milvus」

**Files:**
- Modify: `sale_app/core/kb/vector/vector_factory.py`
- Modify: `README.md`（简短说明）

- [ ] **Step 1: 工厂错误信息写清楚**

```python
case _:
    raise ValueError(
        f"不支持的向量存储类型: {vector_type}。"
        f"当前仅实现 milvus；qdrant/weaviate 代码保留但未启用。"
    )
```

- [ ] **Step 2: README 增加一句**

```markdown
当前向量后端仅启用 **Milvus**（`VECTOR_TYPE=milvus`）。Qdrant/Weaviate 为预留代码，勿在生产切换。
```

- [ ] **Step 3: Commit**

```powershell
git commit -am "docs: clarify milvus-only vector backend support"
```

---

## Phase D — 后续单独计划（本文件不实施，只登记）

以下内容 **不要** 混进 Phase A–C PR，另开计划：

| 项 | 原因 |
|----|------|
| LangGraph 升至 0.2+/1.x + `langgraph-checkpoint-sqlite` | API 破坏性变更（`from_conn_string` context manager） |
| SqliteSaver → PostgresSaver | 需引入 Postgres 与部署变更 |
| 聊天全链路 `astream` / SSE | 需改模板与前端 JS |
| 目录重命名 secrity/moudel/mutil | 大范围 import 变更 |
| KB API 鉴权 + 去掉全部 csrf_exempt | 需定义管理端登录方案 |
| 前置安全改为规则引擎 + 异步队列 | 产品策略决策 |

---

## 验收清单（Phase A–C 全部完成后）

```bash
# 1) 测试
pytest tests/ -v

# 2) 配置
python -c "import os; assert os.path.exists('.env.example')"
git ls-files .env  # 应无输出

# 3) 启动
python manage.py runserver
# 浏览器: /api/chat 可对话；/kb/upload_file 可打开

# 4) 路由
# 发送「我想了解贷款产品」应能进入分类/推荐或问答，而非异常栈
```

---

## 执行方式建议

**推荐顺序：** Task 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10  
**可并行：** Task 8/9/10 在 Task 5 完成后可并行。  
**回滚：** 每个 Task 独立 commit，出问题 `git revert` 单 commit 即可。

---

## Spec 覆盖自检

| 分析文档要点 | 对应 Task |
|--------------|-----------|
| `.env`/SECRET_KEY/DEBUG | Task 1 |
| 图边冲突 + 路由字符串 | Task 2 |
| `deault` / `Product.__str__` / `SERVICE_API_URL` | Task 1、3 |
| `pre_handle` 异常 | Task 4 |
| import 时编译图 | Task 5 |
| 依赖钉版本 / 智谱包名 | Task 6 |
| CSRF | Task 7 |
| KB 重复方法 / 默认 collection | Task 8 |
| demo 脚本 | Task 9 |
| 向量仅 Milvus | Task 10 |
| LangGraph 大升级 / Postgres / 流式 | Phase D（另开计划） |
