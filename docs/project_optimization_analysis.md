# 项目整体分析与优化建议

> 分析时间：2026-09-03  
> 项目：`langgraph_fly_base`（Django + LangGraph 贷款客服 / 知识库）

## 结论

这是一个 **Django 薄 Web 层 + LangGraph 多智能体客服工作流 + Milvus 混合检索知识库** 的贷款场景原型。主链路能跑通，但依赖偏旧、同步阻塞严重、向量「多后端」名存实亡，离生产还有一段距离。

---

## 一、目录结构概览

| 路径 | 职责 |
|------|------|
| `fly_base/` | Django 工程配置（`settings.py` / `urls.py` / WSGI） |
| `sale_app/chat_api/` | HTTP 视图：聊天、KB 上传/检索、图片预览 |
| `sale_app/core/handle_core.py` | 对话编排入口：安全前置 → LangGraph |
| `sale_app/core/mutil/` | LangGraph 主图 / 推荐子图 / 问题修复（拼写应为 multi） |
| `sale_app/core/agent/` | 各业务节点：分类、闲聊、意图、信息收集、QA、推荐 |
| `sale_app/core/prompt/` | Prompt 模板与路由文案 |
| `sale_app/core/moudel/` | LLM 封装（拼写应为 model） |
| `sale_app/core/kb/` | 知识库：loader + `kb_sevice` + vector 抽象 |
| `sale_app/core/kb/vector/milvus/` | **实际在用**的向量实现（混合检索） |
| `sale_app/core/kb/vector/qdrant_vector/` | Qdrant：整文件注释或旁路工具函数 |
| `sale_app/core/kb/vector/weaviate_vector/` | Weaviate：整文件注释掉 |
| `sale_app/core/embedding/` | SPLADE 稀疏向量 |
| `sale_app/secrity/` | 前置安全 + 脱敏（拼写应为 security） |
| `sale_app/config/` | 自定义 Logger |
| `sale_app/util/` | TraceId、UUID、历史格式化、找项目根 |
| `sale_app/database/` | 产品查询（SQLite ORM + 向量混合检索） |
| `config.py`（根目录） | 向量库等环境变量默认值 |
| `docker/` | Milvus / Qdrant compose |
| `templates/` / `static/` | 聊天与 KB 管理页面 |
| `import_data_to_sqlite.py` | 初始化产品数据脚本 |

---

## 二、整体架构与执行流程

```text
浏览器 POST /api/chat
  → to_chat (@csrf_exempt)
  → flow_control()
       ├─ pre_handle()          # LLM 前置安全分类（同步）
       └─ run_flow()            # LangGraph + SqliteSaver
            问题修复 → 问题分类 → 条件路由
              ├─ 闲聊经理
              ├─ 意图确认
              ├─ 信息收集 →（可选脱敏）→ 产品推荐子图
              └─ 产品解答专家 → KB/Milvus RAG → END
  → 渲染 chat.html
```

KB 旁路（不经 LangGraph）：

- `/kb/upload_file` → `KBService.parse` → `Vector` → Milvus `hybrid_add_documents`
- `/kb/search` → similarity / hybrid / keyword
- `/kb/text_insert_milvus` → 产品文本解析入库

### 核心入口示意

```python
# sale_app/core/handle_core.py
def flow_control(question: str, sessionId: str):
    pre_data = pre_handle(question)  # 每次必打一次 LLM
    if pre_data:
        return [HumanMessage(content=question), AIMessage(content=pre_data)]
    data = run_flow(question, {"configurable": {"thread_id": sessionId}})
    return [m for m in data["messages"] if isinstance(m, (AIMessage, HumanMessage))]
```

### 关键文件一览

| 文件 | 用途 |
|------|------|
| `manage.py` | Django 入口，启动前 `load_dotenv` |
| `fly_base/settings.py` | Django 配置、SQLite、静态/媒体、TraceId 中间件 |
| `fly_base/urls.py` | 路由：chat / KB / 图片预览 |
| `config.py` | 向量库与集合名等环境默认配置 |
| `sale_app/chat_api/api.py` | 聊天 HTTP 入口 |
| `sale_app/chat_api/kb_api.py` | 知识库上传、检索、建库、文本入库 |
| `sale_app/core/handle_core.py` | 安全前置 + 调用 LangGraph |
| `sale_app/core/mutil/flow_graph.py` | 主 StateGraph、checkpoint、路由与 compile |
| `sale_app/core/mutil/recommend_product_graph.py` | 产品推荐子图 |
| `sale_app/core/agent/qa_handle.py` | RAG 产品解答 |
| `sale_app/core/moudel/zhipuai.py` | ChatOpenAI/智谱 Embedding 封装 |
| `sale_app/core/kb/kb_sevice.py` | KB 业务门面 |
| `sale_app/core/kb/vector/vector_factory.py` | 按 VECTOR_TYPE 选实现（现仅 Milvus） |
| `sale_app/secrity/pre_safety.py` | 对话前置内容安全分类 |
| `sale_app/secrity/sensitive_info.py` | PII 脱敏 |
| `requirements.txt` | Python 依赖声明 |

---

## 三、框架层建议

| 现状 | 建议 |
|------|------|
| Django 5.x + 同步视图调 LLM | 对话 API 改为 **异步**（ASGI/`async def`）或拆到 **FastAPI/Celery**，避免占满 worker |
| 几乎全接口 `@csrf_exempt`、无鉴权 | 恢复 CSRF；聊天/KB 加 Session/JWT；管理接口单独鉴权 |
| `SECRET_KEY` 写死、`DEBUG=True` | 全部走环境变量；生产关 DEBUG、配 `ALLOWED_HOSTS` |
| SQLite 业务库 + SqliteSaver 会话 | 业务库可先留 SQLite；会话 checkpoint 生产用 **PostgresSaver** |
| Django 当全栈 UI | 原型可保留；若要做正式产品，API/前端分离更清晰 |

### 流式输出示例（减少首字延迟）

```python
# 建议：用 StreamingHttpResponse / SSE，而不是一次 invoke 再整页渲染
async def to_chat_stream(request):
    async for event in chain.astream_events(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": session_id}},
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            yield event["data"]["chunk"].content
```

---

## 四、依赖包版本建议

当前 `requirements.txt` 大致停留在 **2024 中期**：

```text
Django                 # 未钉版本
langchain ~=0.2.1
langgraph ~=0.0.55
langchain-zhipuai      # 与代码 import langchain_zhipu 不一致
```

### 优先修复

1. **钉死版本**，避免 `pip install` 漂移：`Django==5.0.x`、各 langchain 包写死。
2. **包名对齐**：代码是 `from langchain_zhipu import ...`，requirements 写 `langchain-zhipuai`，安装后易 `ImportError`。
3. **补齐隐藏依赖**：`fasttext`、`scipy`、`spacy`/Presidio 语言模型（`sensitive_info` 启动即加载）。
4. **LangGraph 升级分阶段**（不要一次跳到最新硬改）：
   - 短期：先修图逻辑与配置，保持 `0.0.55` 可运行；
   - 中期：升到 `langgraph>=0.2` + `langgraph-checkpoint-sqlite`（`from_conn_string` 已变 **context manager**）；
   - 生产：`PostgresSaver` / `AsyncPostgresSaver`，放弃高并发下的 SqliteSaver。
5. **Pydantic**：代码大量 `langchain_core.pydantic_v1` 和 `deault=` 拼写错误，升级时一并改成正确的 `Field(default=...)`。

### 升级后 checkpoint 写法示例

```python
# langgraph >= 0.2 典型用法（示意）
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("storage/memory_file/chat_history.db") as memory:
    chain = flow_graph.compile(checkpointer=memory)
```

### 建议依赖声明示例（示意，需实测锁定）

```text
Django==5.0.6
langchain==0.2.16
langchain-core==0.2.38
langchain-community==0.2.16
langchain-openai==0.1.23
langgraph==0.0.55
python-dotenv==1.0.1
# 包名需与实际 import 对齐后再锁定
# langchain-zhipu / langchain-zhipuai
qdrant-client
langchain-qdrant
weaviate-client
langchain-milvus
pymilvus[model]
pandas
openpyxl
docx
xlrd
unstructured[docx]==0.10.30
presidio-anonymizer
presidio-analyzer
Faker
langdetect
# fasttext  # Windows 建议本地 wheel
# scipy / spacy  # SPLADE、脱敏按需补齐
```

---

## 五、代码执行流程优化（高优先级）

### 1. 图边冲突（会影响路由）

`flow_graph.py` 中存在：

```python
for node in list(flow_graph.nodes.keys()):
    flow_graph.add_edge(node, END)

flow_graph.add_conditional_edges("信息收集", information_router, {
    "FINISH": END,
    "产品推荐": "产品推荐",
})
```

给**所有节点**无条件连 `END`，再叠条件边，容易和预期路由打架。应只给「终态节点」连 `END`，其余用 `add_conditional_edges` 明确下一跳。

### 2. 路由字符串不一致

`decide_router` 里判断 `"产品问答"`，图节点名是 `"产品解答专家"`，相关分支可能永远不生效。建议统一枚举常量：

```python
class NextNode:
    QA = "产品解答专家"
    RECOMMEND = "产品推荐"
    GATHER = "信息收集"
    CHAT = "闲聊经理"
    INTENT = "意图确认"
```

### 3. 模块 import 时就建 LLM / 编译图

`flow_graph.py`、`recommend_product_graph.py` 在 import 时执行 `ZhipuAI().openai_chat()` 和 `compile()`。应改为工厂函数懒加载，便于测试和多进程：

```python
_chain = None

def get_chain():
    global _chain
    if _chain is None:
        llm = ZhipuAI().openai_chat()
        # build + compile...
        _chain = flow_graph.compile(checkpointer=memory)
    return _chain
```

### 4. 前置安全每次调 LLM 过重

`pre_handle` 对每条消息做 structured output，成本高且慢。可改为：规则/关键词初筛 → 可疑再 LLM；或接入独立内容安全 API。

### 5. 视图层同步阻塞

一次聊天可能串行：**安全 LLM → 问题修复 → 分类 → 业务节点（+ RAG）**，Django 同步视图会长时间占连接。至少改为 `asyncio`/`astream`，或把重任务丢队列。

---

## 六、知识库 / 向量层

| 后端 | 状态 | 评价 |
|------|------|------|
| **Milvus** | 唯一工厂启用路径 | 功能最完整：稠密+SPLADE 稀疏、混合检索、分区键；连接生命周期与 index 度量仍可优化 |
| **Qdrant** | 工厂 case 注释掉 | 未实现可热切换 |
| **Weaviate** | 整文件注释 | 死代码，依赖仍在 requirements |

### 建议

- 工厂只启用 Milvus，Qdrant/Weaviate 基本是死代码 → **要么删掉，要么真正实现 `BaseVector` 并注册**。
- 默认集合名 `'test_json'` 散落业务代码 → 统一配置中心。
- Milvus 分区过滤字符串拼接有注入风险 → 用参数化/白名单。
- `KBService.parse` 与 `parse_excel` 重复 → 合并为一个入口。

---

## 七、代码异味与技术债

### 命名拼写（广泛存在）

- `secrity` → security
- `moudel` → model
- `mutil` → multi
- `kb_sevice` → kb_service
- `history_formate` → format
- `cicile_attribute` → cycle
- `deault=`（Pydantic Field 多处，应为 `default`）

### 重复 / 死代码

- `KBService.parse` 与 `parse_excel` 几乎完全重复
- `handle_core` 导入 `sensitive_info_anonymize` 但未使用
- `api.py` 导入 `cache` / `JsonResponse` / `json` 未使用
- Qdrant/Weaviate 大段注释死代码

### 安全硬编码 / 配置

- `settings.py`：`SECRET_KEY` 写死、`DEBUG=True`、`ALLOWED_HOSTS=[]`
- **`.env` 若已被 git 跟踪**（含 API Key）→ 必须轮换密钥并移出版本库
- 几乎所有 API `@csrf_exempt`，无鉴权
- Milvus 分区过滤用字符串拼接：`like '%{partition_key}%'`（注入面）

### 其他 bug 信号

- `Product.__str__` 里 `print` 而非 `return`
- `config.DEFAULTS['SERVICE_API_URL']` 带多余 `=`：`'=http://...'`
- `pre_handle` 异常处理脆弱：`return e.body.get("message")`
- `image_preview` 路径拼接缺少规范化校验

### 不宜留在生产路径的 demo/test

| 文件 | 原因 |
|------|------|
| `sale_app/core/mutil/demo.py` | 模块级执行 LangSmith `evaluate(...)`，import 即跑评测 |
| `sale_app/secrity/test.py` | 脱敏实验脚本 + 样例 PII |
| `sale_app/core/kb/vector/milvus/test.py` | SPLADE 本地试验脚本 |
| Qdrant/Weaviate 整文件注释实现 | 死代码 |

---

## 八、建议落地顺序

| 优先级 | 事项 | 收益 |
|--------|------|------|
| P0 | 密钥/DEBUG/CSRF/鉴权；`.env` 出库 | 安全 |
| P0 | 修图边 + 路由常量；`deault` 等明显 bug | 正确性 |
| P1 | 钉版本 + 对齐 `langchain_zhipu`；补依赖 | 可安装可复现 |
| P1 | 聊天接口流式/异步；前置安全轻量化 | 体验与吞吐 |
| P2 | 向量抽象瘦身（只留 Milvus）或补齐多后端 | 可维护性 |
| P2 | LangGraph 升 0.2+，checkpoint 迁 Postgres | 生产就绪 |
| P3 | 目录重命名、删死代码、补测试与观测（LangSmith/Langfuse） | 长期演进 |

---

## 九、附录：安全模块说明

当前「安全」**不是** Django Middleware，而是业务函数：

1. **`pre_safety.pre_handle`**（每次聊天必调）  
   - LLM structured output 打标：涉政、公安、编程、翻译、创作等  
   - 问题：依赖 LLM 自身、贵且慢；异常处理脆弱  

2. **`sensitive_info.sensitive_info_anonymize`**  
   - fasttext 语种 + Presidio 可逆脱敏  
   - **仅**在信息收集且环境变量开启时调用  
   - 模块 import 即加载模型，启动重、与 requirements 脱节  

TraceId 中间件（`traceid_ware`）只做日志关联，无安全能力。
