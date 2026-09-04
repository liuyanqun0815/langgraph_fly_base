import os
import shutil

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from app.templates_env import templates
from config import kb_file_root

router = APIRouter()


def _save_upload(upload: UploadFile) -> str:
    os.makedirs(kb_file_root(), exist_ok=True)
    dest = os.path.join(kb_file_root(), upload.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return dest


@router.get("/kb/upload_file", response_class=HTMLResponse)
async def upload_file_get(request: Request):
    return templates.TemplateResponse(request, "upload_document.html", {})


@router.post("/kb/upload_file")
async def upload_file_post(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    upload_type: str = Form("general"),
):
    from sale_app.core.kb.kb_sevice import KBService

    if not file.filename:
        return PlainTextResponse("excel_file is null", status_code=400)
    absolute_path = _save_upload(file)
    try:
        if upload_type == "general":
            KBService.parse(absolute_path, collection_name)
        else:
            KBService.xlsx_qa_upload(absolute_path, collection_name)
    except ValueError as exc:
        return PlainTextResponse(str(exc), status_code=400)
    return PlainTextResponse("文件上传成功！")


@router.get("/kb/search", response_class=HTMLResponse)
async def search_get(request: Request):
    context = {"response": ""}
    return templates.TemplateResponse(request, "recall_test.html", context)


@router.post("/kb/search", response_class=HTMLResponse)
async def search_post(
    request: Request,
    collection_name: str = Form(...),
    query: str = Form(...),
    file_name: str = Form(""),
    query_type: str = Form(...),
):
    from sale_app.core.kb.kb_sevice import KBService

    if query_type == "vector":
        data = KBService.similarity_search(query, collection_name, file_name)
    elif query_type == "hybrid_search":
        data = KBService.hybrid_search(query, collection_name, file_name)
    elif query_type == "keyword_search":
        data = KBService.keyword_search(query, collection_name, file_name)
    else:
        data = []

    context = {
        "response": {
            "collection": collection_name,
            "file": file_name,
            "search": query,
            "results": data,
            "message": "搜索结果如下：",
        }
    }
    return templates.TemplateResponse(request, "recall_test.html", context)


@router.get("/kb/create_collection", response_class=HTMLResponse)
async def create_collection_get(request: Request):
    return templates.TemplateResponse(request, "create_collection.html", {})


@router.post("/kb/create_collection", response_class=HTMLResponse)
async def create_collection_post(request: Request, collection_name: str = Form(None)):
    from sale_app.core.kb.kb_sevice import KBService

    if not collection_name:
        return PlainTextResponse("collection_name is null", status_code=400)
    KBService.create_collection(collection_name)
    return templates.TemplateResponse(request, "create_collection.html", {"message": "创建成功"})


@router.post("/kb/upload_and_read_excel")
async def upload_and_read_excel(
    excel_file: UploadFile = File(...),
    collection_name: str | None = Query(None),
):
    from sale_app.core.kb.kb_sevice import KBService

    absolute_path = _save_upload(excel_file)
    KBService.parse_excel(absolute_path, collection_name)
    return JSONResponse({"data": "sucess"})


@router.post("/kb/text_insert_milvus")
async def text_insert_milvus(
    text: str = Form(...),
    collection_name: str | None = Form(None),
):
    from sale_app.core.kb.kb_sevice import KBService

    KBService.text_insert(text, collection_name or None)
    return JSONResponse({"data": "sucess"})
