from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from sale_app.config.log import Logger
from sale_app.core.handle_core import flow_control
from sale_app.util.UUIDUtils import generate_random_string

logger = Logger("fly_base")


@csrf_exempt
def to_chat(request):
    body_unicode = request.body.decode("utf-8")
    body_data = json.loads(body_unicode)
    chat = body_data.get("chat")
    session_id = body_data.get("sessionId")
    if chat is None:
        return JsonResponse({"data": ""})
    if session_id is None:
        return JsonResponse({"msg": "sessionId is required"})
    if cache.has_key(session_id):
        threadId = cache.get(session_id)
    else:
        threadId = generate_random_string(11)
        cache.set(session_id, threadId)
    flow_control(chat, threadId)
    return HttpResponse({"message": "Hello, world!"})
