import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .forms.excel_form import ExcelUploadForm
from .forms.file_upload_form import FileUploadForm

from ..config.log import Logger
from ..core.kb.kb_sevice import KBService

logger = Logger("fly_base")


# xlsx文件上传
class DocumentForm:
    pass


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            if not excel_file:
                return HttpResponse("excel_file is null")
            collection_name = request.FILES("collection_name")
            # 使用 FileSystemStorage 来保存文件到指定目录
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'kb_file'))
            filename = fs.save(excel_file.name, excel_file)
            # 获取文件的URL路径
            absolute_path = os.path.join(fs.base_location, filename)
            upload_type = request.FILES("upload_type")
            if upload_type == 'general':
                KBService.parse(absolute_path)
            else:
                KBService.xlsx_qa_upload(absolute_path, collection_name)
            return HttpResponse('文件上传成功！')
    else:
        form = DocumentForm()
    return render(request, 'upload_file.html', {'form': form})


@csrf_exempt
def search(request):
    query = request.GET.get('query')
    collection_name = request.GET.get("collection_name")
    file_name = request.GET.get("file_name")
    data = KBService.similarity_search(query, collection_name, file_name)
    json = {
        "data": data.__str__()
    }
    return JsonResponse(json)


@csrf_exempt
def create_collection_api(request):
    collection_name = request.GET.get("collection_name")
    if not collection_name:
        return HttpResponse("collection_name is null")
    KBService.create_collection(collection_name)
    return HttpResponse("create index success")


@csrf_exempt
def upload_and_read_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            collection_name = request.GET.get("collection_name")
            # 使用 FileSystemStorage 来保存文件到指定目录
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'kb_file'))
            filename = fs.save(excel_file.name, excel_file)
            # 获取文件的URL路径
            # fs.base_location = settings.MEDIA_ROOT
            # file_url = fs.url(filename)
            absolute_path = os.path.join(fs.base_location, filename)
            KBService.parse_excel(absolute_path, collection_name)
    return JsonResponse({'data': 'sucess'})


@csrf_exempt
def text_insert_milvus(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        collection_name = request.POST.get("collection_name", None) or None
        KBService.text_insert(text, collection_name)
    return JsonResponse({'data': 'sucess'})


@csrf_exempt
def hybrid_search(request):
    query = request.GET.get('query')
    collection_name = request.GET.get("collection_name")
    file_name = request.GET.get("file_name")

    data = KBService.hybrid_search(query, collection_name, file_name)
    json = {
        "data": data.__str__()
    }
    return JsonResponse(json)


@csrf_exempt
def keyword_search(request):
    query = request.GET.get('query')
    collection_name = request.GET.get("collection_name")
    file_name = request.GET.get("file_name")

    data = KBService.keyword_search(query, collection_name, file_name)
    json = {
        "data": data.__str__()
    }
    return JsonResponse(json)
