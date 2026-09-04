from config import get_env


def test_service_api_url_has_no_leading_equals():
    url = get_env("SERVICE_API_URL")
    assert url.startswith("http")
    assert not url.startswith("=")
