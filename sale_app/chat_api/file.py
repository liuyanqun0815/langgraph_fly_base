import os

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import mimetypes
from sale_app.config.log import Logger

logger = Logger("fly_base")


@csrf_exempt
def image_preview(request, fileName: str):
    image_file_path = os.path.join(settings.IMAGE_URL, fileName)
    # 判断文件是否存在
    if not os.path.exists(image_file_path):
        logger.info(f'Image file not found: {image_file_path}', )
        raise FileNotFoundError(f'Image file not found: {image_file_path}')

    mime_type, _ = mimetypes.guess_type(image_file_path)
    with open(image_file_path, 'rb') as image_file:
        return HttpResponse(image_file.read(), content_type=mime_type)
