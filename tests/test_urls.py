import sys
from unittest.mock import MagicMock

_mock_handle_core = MagicMock()
_mock_handle_core.flow_control = MagicMock(return_value=[])
sys.modules.setdefault("sale_app.core.handle_core", _mock_handle_core)
sys.modules.setdefault("fasttext", MagicMock())

from django.urls import path

from sale_app.chat_api.api import to_chat

urlpatterns = [
    path("api/chat", to_chat, name="chat"),
]
