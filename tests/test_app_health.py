from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


@patch("app.main.shutdown_chain")
@patch("app.main.startup_chain")
def test_health(mock_startup_chain, mock_shutdown_chain):
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    mock_startup_chain.assert_called_once()
    mock_shutdown_chain.assert_called_once()
