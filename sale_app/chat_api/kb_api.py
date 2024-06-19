import os

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .forms import DocumentForm

from ..config.log import Logger
from ..core.kb.vector.qdrant_vector import create_collection
from ..core.kb.xlsx_qa_view import xlsx_qa_upload

logger = Logger("fly_base")


# xlsx文件上传
@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            file_doc = request.FILES['document']
            file_extension = os.path.splitext(file_doc.name)[1].lower()
            if file_extension == '.xlsx':
                xlsx_qa_upload(file_doc)
            else:
                return HttpResponse(f'文件格式错误！目前不支持{file_extension}')
            return HttpResponse('文件上传成功！')
    else:
        form = DocumentForm()
    return render(request, 'upload.html', {'form': form})


@csrf_exempt
def create_index(request):
    collection_name = request.GET.get("collection_name")
    if not collection_name:
        return HttpResponse("collection_name is null")
    create_collection(collection_name)
    return HttpResponse("create index success")