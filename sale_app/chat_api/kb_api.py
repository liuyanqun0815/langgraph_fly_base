import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .forms.excel_form import ExcelUploadForm
from .forms.file_upload_form import FileUploadForm, SearchForm

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
            excel_file = form.cleaned_data['file']
            if not excel_file:
                return HttpResponse("excel_file is null")
            collection_name = form.cleaned_data['collection_name']
            # 使用 FileSystemStorage 来保存文件到指定目录
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'kb_file'))
            filename = fs.save(excel_file.name, excel_file)
            # 获取文件的URL路径
            absolute_path = os.path.join(fs.base_location, filename)
            upload_type = form.cleaned_data['upload_type']
            if upload_type == 'general':
                KBService.parse(absolute_path)
            else:
                KBService.xlsx_qa_upload(absolute_path, collection_name)
            return HttpResponse('文件上传成功！')
    else:
        form = DocumentForm()
    return render(request, 'upload_document.html', {'form': form})


@csrf_exempt
def search(request):
    global data
    form = SearchForm(request.POST or None)
    context = {
        'form': form,
        'response': ''
    }
    if request.method == 'GET':
        return render(request, 'recall_test.html', context)
    collection_name = form.data['collection_name']
    query = form.data['query']
    file_name = form.data["file_name"]
    query_type = form.data['query_type']
    if query_type == 'vector':
        data = KBService.similarity_search(query, collection_name, file_name)
    elif query_type == 'hybrid_search':
        data = KBService.hybrid_search(query, collection_name, file_name)
    elif query_type == 'keyword_search':
        data = KBService.keyword_search(query, collection_name, file_name)

    # 将结果添加到上下文
    context['response'] = {
        'collection': collection_name,
        'file': file_name,
        'search': query,
        'results': data,
        'message': '搜索结果如下：',
    }
    return render(request, 'recall_test.html', context)


@csrf_exempt
def create_collection_api(request):
    if request.method == 'POST':
        collection_name = request.POST.get("collection_name")
        if not collection_name:
            return HttpResponse("collection_name is null")
        KBService.create_collection(collection_name)
        return render(request, 'create_collection.html', {'message': '创建成功'})
    return render(request, 'create_collection.html')


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






