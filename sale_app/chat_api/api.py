from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json

from sale_app.chat_api.forms.chat_form import ChatForm
from sale_app.config.log import Logger
from sale_app.core.handle_core import flow_control
from sale_app.util.UUIDUtils import generate_random_string

logger = Logger("fly_base")


@csrf_exempt
def to_chat(request):
    form = ChatForm(request.POST or None)
    form_data = {
        'form': form,
        'content': ''
    }
    if request.method == "GET":
        return render(request, 'chat.html', form_data)

    chat = form.data["chat"]
    session_id = form.data.get("sessionId", "")
    if session_id is None or session_id == "":
        session_id = generate_random_string(11)
    data = flow_control(chat, session_id)
    # 清空表单中的chat字段
    form = ChatForm(initial={'sessionId': session_id})
    form_data['form'] = form
    form_data['data'] = data
    form_data['message'] = "执行成功"
    return render(request, 'chat.html', form_data)
