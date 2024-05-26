from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def to_chat(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponse({"message": "Invalid JSON body"})

    logger.info("请求参数：{}".format(body))
    return HttpResponse({"message": "Hello, world!"})
