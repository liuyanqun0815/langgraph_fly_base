from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


@patch("app.main.shutdown_chain")
@patch("app.main.startup_chain")
def test_upload_page_get(mock_startup_chain, mock_shutdown_chain):
    with TestClient(app) as client:
        assert client.get("/kb/upload_file").status_code == 200


@patch("app.main.shutdown_chain")
@patch("app.main.startup_chain")
def test_search_page_get(mock_startup_chain, mock_shutdown_chain):
    with TestClient(app) as client:
        assert client.get("/kb/search").status_code == 200


@patch("app.main.shutdown_chain")
@patch("app.main.startup_chain")
def test_create_collection_get(mock_startup_chain, mock_shutdown_chain):
    with TestClient(app) as client:
        assert client.get("/kb/create_collection").status_code == 200
