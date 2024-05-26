from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from sale_app.config.log import Logger

logger = Logger("fly_base")


@csrf_exempt
def to_chat(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponse({"message": "Invalid JSON body"})

    logger.info(f"请求参数：{body}")
    return HttpResponse({"message": "Hello, world!"})
