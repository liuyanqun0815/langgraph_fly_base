import os

import django
from django.conf import settings


def test_service_api_url_has_no_leading_equals():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fly_base.settings")
    if not settings.configured:
        django.setup()
    from config import get_env

    url = get_env("SERVICE_API_URL")
    assert url.startswith("http"), url
    assert not url.startswith("="), url
