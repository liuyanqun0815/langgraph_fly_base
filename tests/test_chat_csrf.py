import os
import sys
from unittest.mock import MagicMock, patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fly_base.settings")

_mock_handle_core = MagicMock()
_mock_handle_core.flow_control = MagicMock(return_value=[])
sys.modules.setdefault("sale_app.core.handle_core", _mock_handle_core)
sys.modules.setdefault("fasttext", MagicMock())

import django
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, override_settings

django.setup()

TEST_SETTINGS = {
    "ROOT_URLCONF": "tests.test_urls",
    "ALLOWED_HOSTS": ["testserver", "127.0.0.1", "localhost"],
}


def test_chat_post_without_csrf_token_returns_403():
    with override_settings(**TEST_SETTINGS):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/api/chat", {"chat": "hello"})
    assert response.status_code == 403


def test_chat_post_with_csrf_token_returns_200():
    with override_settings(**TEST_SETTINGS):
        client = Client(enforce_csrf_checks=True)
        csrf_request = RequestFactory().get("/api/chat")
        csrf_token = get_token(csrf_request)
        client.cookies["csrftoken"] = csrf_token
        with patch("sale_app.chat_api.api.flow_control", return_value=[]) as mock_flow:
            with patch("sale_app.chat_api.api.render", return_value=HttpResponse("ok")):
                response = client.post(
                    "/api/chat",
                    {"chat": "hello", "csrfmiddlewaretoken": csrf_token},
                )
            mock_flow.assert_called_once()
    assert response.status_code == 200
